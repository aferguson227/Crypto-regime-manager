#!/usr/bin/env python3
"""V43 material decision briefing / inbox.

Builds stable material-event IDs from the current validated CRM state. The web
client remembers which event IDs the user has acknowledged in browser storage,
so the opening briefing appears only when something genuinely new is present.
No trading state is mutated.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'decision_inbox.json'

def load(name):
    try:
        x=json.loads((DOCS/name).read_text(encoding='utf-8-sig')); return x if isinstance(x,dict) else {}
    except Exception:return {}

def event(kind,title,detail,severity='info',action=None,payload=None):
    material={'kind':kind,'title':title,'detail':detail,'action':action,'payload':payload or {}}
    eid=hashlib.sha256(json.dumps(material,sort_keys=True,default=str).encode()).hexdigest()[:24]
    return {'event_id':eid,'kind':kind,'title':title,'detail':detail,'severity':severity,'action':action,'payload':payload or {}}

def build():
    ws=load('professional_workspace.json'); expansion=load('expansion_readiness.json'); trades=load('trade_intelligence.json')
    market=load('market_intelligence.json'); capital=load('capital_intelligence.json'); issues=load('issues.json')
    rec=load('recommendation_intelligence.json'); pipeline=load('research_pipeline.json')
    items=[]
    d=ws.get('daily_decision') or {}
    if d.get('bot_name'):
        items.append(event('PRIMARY_DECISION',f"{str(d.get('action') or 'WAIT').replace('_',' ').title()}: {d.get('bot_name')}",
            f"Confidence {d.get('confidence_pct')}%. " + ('; '.join(d.get('why') or [])[:260] or 'Current governed recommendation.'),
            'action' if d.get('action') in {'DEPLOY_TODAY','PAUSE_NEW_DEALS'} else 'info','REVIEW_DECISION',d))
    for ch in ws.get('what_changed') or []:
        items.append(event('CONFIG_CHANGE',f"{ch.get('field')} changed",f"{ch.get('before')} → {ch.get('after')}",'action','REVIEW_DCA',ch))
    if expansion.get('state')=='READY_FOR_MANUAL_REVIEW' and expansion.get('candidate'):
        c=expansion['candidate']; asset=c.get('asset') or expansion.get('recommended_next_candidate')
        items.append(event('NEW_CANDIDATE',f'{asset}/USDT ready for manual review',
            expansion.get('next_action') or 'All expansion gates passed.', 'opportunity','ADD_RECOMMENDED_BOT',
            {'asset':asset,'candidate':c,'score_pct':expansion.get('score_pct'),'deployable_capital':expansion.get('deployable_capital')}))
    for t in trades.get('trades') or []:
        if t.get('monitoring_state') not in {None,'MONITOR'}:
            items.append(event('TRADE_ATTENTION',f"{t.get('bot_name') or t.get('asset')} needs attention",
                f"{str(t.get('monitoring_state')).replace('_',' ').title()} · P/L {t.get('profit_pct')}% · hold {t.get('hold_hours')}h",
                'warning','REVIEW_TRADE',t))
    # Only surface genuine active issues.
    for it in (issues.get('issues') or [])[:6]:
        if not isinstance(it,dict): continue
        sev=str(it.get('severity') or 'warning').lower()
        items.append(event('SYSTEM_ISSUE',it.get('title') or 'System issue',it.get('detail') or '',sev,'REVIEW_SYSTEM',it))
    # Market regime is important context, but not a pop-up trigger by itself unless it changed in workspace history.
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'mode':'material_decision_inbox','items':items,'material_count':len(items),
      'opening_briefing_policy':'Show only event IDs not acknowledged in this browser.',
      'read_only':True,'manual_approval_required':True,
      'guardrails':{'live_bot_mutations':False,'order_mutations':False,'browser_acknowledgement_only':True}}
    payload['snapshot_id']=hashlib.sha256(json.dumps([x['event_id'] for x in items],sort_keys=True).encode()).hexdigest()[:24]
    return payload

def main():
    OUT.write_text(json.dumps(build(),indent=2),encoding='utf-8'); print(f'Decision inbox written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
