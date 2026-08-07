#!/usr/bin/env python3
"""V43 recommended-bot candidate builder.

Produces review-ready DCA packages from independently validated research
candidates. Promotion is advisory only; the website may save a recommendation
in browser storage or download its JSON package, but cannot create a live bot.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'recommended_bots.json'

def load(n):
    try:
        x=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return x if isinstance(x,dict) else {}
    except Exception:return {}

def num(v):
    try:return float(v) if v not in (None,'') else None
    except:return None

def canonical_settings(raw):
    raw=raw or {}
    aliases={
      'base_order_volume':['base_order_volume','base_order'],
      'safety_order_volume':['safety_order_volume','safety_order'],
      'take_profit_pct':['take_profit_pct','take_profit'],
      'so_deviation_pct':['so_deviation_pct','safety_order_deviation_pct','safety_order_step_percentage'],
      'safety_orders':['safety_orders','max_safety_orders'],
      'volume_scale':['volume_scale','martingale_volume_coefficient'],
      'step_scale':['step_scale','martingale_step_coefficient'],
      'max_active_safety_orders':['max_active_safety_orders'],
      'max_active_deals':['max_active_deals'],
      'start_condition':['start_condition'],
      'order_type':['order_type'],
      'trailing_enabled':['trailing_enabled'],
      'cooldown_seconds':['cooldown_seconds']}
    out={}
    for key,names in aliases.items():
        out[key]=next((raw.get(n) for n in names if raw.get(n) is not None),None)
    return out

def profitability(c):
    q=c.get('q1_2026_metrics') or {}; tr=c.get('training_metrics') or {}
    def roc(m):
        pnl=num(m.get('net_pnl')); cap=num(m.get('max_capital'))
        return round(100*pnl/cap,1) if pnl is not None and cap and cap>0 else None
    qroc=roc(q); troc=roc(tr)
    return {'q1_return_on_max_capital_pct':qroc,'training_return_on_max_capital_pct':troc,'q1_net_pnl':num(q.get('net_pnl')),'q1_closed_deals':q.get('closed_deals'),'q1_average_hold_hours':num(q.get('average_hours')),'q1_longest_hold_hours':num(q.get('longest_hours')),'label':'Historical validated return on maximum capital; not a future-profit forecast.','worthwhile_indicator':'STRONG_EVIDENCE' if qroc is not None and qroc>=20 else ('POSITIVE_EVIDENCE' if qroc is not None and qroc>0 else 'INSUFFICIENT_EVIDENCE')}

def build():
    expansion=load('expansion_readiness.json'); pipe=load('research_pipeline.json'); live=load('recommendation_intelligence.json')
    deployable=num(expansion.get('deployable_capital'))
    candidates=[]
    for c in pipe.get('candidates') or []:
        if not isinstance(c,dict) or c.get('stage')!='READY_FOR_MANUAL_REVIEW': continue
        asset=str(c.get('asset') or '').upper(); frozen=canonical_settings(c.get('frozen_settings') or {})
        hist_max=num(((c.get('q1_2026_metrics') or {}).get('max_capital'))) or num(((c.get('training_metrics') or {}).get('max_capital')))
        # Pilot sizing is deliberately conservative and advisory: at most 20% of deployable capital and never above historical max-cap evidence.
        suggested=None
        if deployable is not None and deployable>0:
            suggested=round(min(deployable*0.20,hist_max if hist_max and hist_max>0 else deployable*0.20),2)
        completeness=sum(1 for v in frozen.values() if v is not None); total=len(frozen)
        confidence=num(c.get('current_research_score'))
        cid=hashlib.sha256(json.dumps({'asset':asset,'settings':frozen,'stage':c.get('stage')},sort_keys=True,default=str).encode()).hexdigest()[:24]
        candidates.append({'candidate_id':cid,'asset':asset,'pair':c.get('pair') or f'{asset}-USDT','state':'READY_FOR_MANUAL_REVIEW',
          'confidence_pct':confidence,'suggested_pilot_usdt':suggested,'suggested_initial_allocation_usdt':suggested,'historical_max_capital':hist_max,
          'profitability_evidence':profitability(c),
          'dca_settings':frozen,'settings_completeness_pct':round(100*completeness/total,1) if total else 0,
          'kraken_q1_status':c.get('walk_forward_status'),'training_metrics':c.get('training_metrics'),'q1_2026_metrics':c.get('q1_2026_metrics'),
          'evidence_gates':c.get('gates') or {},'manual_approval_required':True,'creates_live_bot':False,
          'promotion_note':'Adding here saves a recommended-bot package only. Optimisation status is tracked automatically; live deployment remains manual.'})
    # Keep strongest first.
    candidates.sort(key=lambda x:(x.get('confidence_pct') or -1,x.get('settings_completeness_pct') or 0),reverse=True)
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'mode':'read_only_recommended_bot_packages','candidate_count':len(candidates),'candidates':candidates,
      'promotion_policy':{'manual_approval_required':True,'browser_save_only':True,'downloadable_configuration':True,'automatic_live_deployment':False},
      'read_only':True}
    payload['snapshot_id']=hashlib.sha256(json.dumps([x['candidate_id'] for x in candidates],sort_keys=True).encode()).hexdigest()[:24]
    return payload

def main():
    OUT.write_text(json.dumps(build(),indent=2),encoding='utf-8'); print(f'Recommended bots written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
