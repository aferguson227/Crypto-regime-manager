#!/usr/bin/env python3
"""Build the V36 decision-first daily workspace from canonical CRM state."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUTPUT=DOCS/'professional_workspace.json'

def load(name):
    try:
        value=json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
        return value if isinstance(value,dict) else {}
    except Exception:return {}

def first(*values):
    return next((v for v in values if v not in (None,'',[],{})),None)

def setting_value(source,*names):
    for name in names:
        if name in source and source[name] is not None:return source[name]
    return None

def build():
    c=load('command_state.json'); previous=load('professional_workspace.json')
    queue=c.get('priority_queue') or []; recs=c.get('recommendations') or []
    top=queue[0] if queue else {}
    rec=next((r for r in recs if r.get('bot_name')==top.get('bot_name')),recs[0] if recs else {})
    comp=rec.get('production_comparison') or {}
    recommended=(comp.get('recommended_settings') or {}).get('values') or {}
    differences=comp.get('differences') or []
    live={d.get('field'):d.get('live_value') for d in differences if d.get('field')}
    production={d.get('field'):d.get('production_value') for d in differences if d.get('field')}
    cap=c.get('capital') or {}; cloud=c.get('cloud') or {}; health=c.get('health') or {}
    portfolio=c.get('portfolio') or {}; market=c.get('market') or {}
    required=first(top.get('capital_required'),cap.get('next_required'))
    deployable=cap.get('deployable')
    settings_order=['base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale','max_active_safety_orders','max_active_deals','start_condition','order_type','trailing_enabled','cooldown_seconds']
    missing=[k for k in settings_order if setting_value(recommended,k) is None]
    blockers=list(top.get('blockers') or [])
    can_fund=top.get('can_fund')
    readiness_checks=[
      {'label':'Bot selected','state':'pass' if top.get('bot_name') else 'fail'},
      {'label':'Allocation known','state':'pass' if required is not None else 'warn'},
      {'label':'Funding confirmed','state':'pass' if can_fund is True else ('fail' if can_fund is False else 'warn')},
      {'label':'DCA settings complete','state':'pass' if not missing else 'warn'},
      {'label':'Cloud data current','state':'pass' if str(cloud.get('overall_status','')).lower() in {'healthy','ok','pass'} else 'warn'},
    ]
    readiness_score=round(100*sum(1 for x in readiness_checks if x['state']=='pass')/len(readiness_checks),1)
    action=top.get('action') or 'WAIT'; confidence=top.get('confidence_pct')
    brief=[]
    if action: brief.append(f"Primary action: {str(action).replace('_',' ').title()} {top.get('bot_name') or '—'}.")
    if required is not None: brief.append(f"Suggested allocation: {required:g} {cap.get('currency') or 'USDT'}.")
    elif deployable is not None: brief.append(f"Deployable capital: {deployable:g} {cap.get('currency') or 'USDT'}; exact allocation remains advisory.")
    else: brief.append('Allocation remains unconfirmed; do not assume funding is available.')
    if missing: brief.append(f"DCA plan needs {len(missing)} more field{'s' if len(missing)!=1 else ''} before it is complete.")
    else: brief.append('The recommended DCA plan is complete for manual review.')
    risks=list(c.get('risks') or [])
    if risks: brief.append(f"Main risk: {risks[0]}")
    changed=[]; old=(previous.get('daily_decision') or {}) if isinstance(previous,dict) else {}
    for key,label in [('bot_name','Bot'),('action','Action'),('confidence_pct','Confidence')]:
        before=old.get(key); after=top.get(key)
        if before is not None and before!=after: changed.append({'field':label,'before':before,'after':after})
    old_settings=previous.get('recommended_settings') or {}
    for key,val in recommended.items():
        if key in old_settings and old_settings.get(key)!=val: changed.append({'field':key,'before':old_settings.get(key),'after':val})
    payload={
      'schema_version':'3.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'read_only':True,'manual_approval_required':True,
      'briefing':brief,
      'daily_decision':{'bot_name':top.get('bot_name'),'asset':top.get('asset'),'action':action,'confidence_pct':confidence,'urgency':top.get('urgency'),'why':list(top.get('rationale') or []),'blockers':blockers},
      'decision_readiness':{'score_pct':readiness_score,'checks':readiness_checks,'ready_for_manual_action':readiness_score==100 and not blockers},
      'allocation':{'required_quote':required,'quote_currency':cap.get('currency') or 'USDT','can_fund':can_fund,'deployable_quote':deployable,'asset_allocations':cap.get('asset_allocations') or [],'display_rule':'Base-asset quantities use the asset ticker; budgets and capital use the quote-currency code.'},
      'recommended_settings':recommended,'settings_order':settings_order,'missing_settings':missing,
      'live_settings':live,'production_settings':production,'setting_differences':differences,
      'what_changed':changed,'risks':risks,'market':market,'portfolio':portfolio,'presentation':{'locale':'en-GB','timezone':'Europe/London','negative_sign':'−','currency_policy':'Use explicit currency codes such as USDT; never assume $ means USDT.','unknown_policy':'Unknown values remain Unknown and are never coerced to zero.'},
      'deployment_health':{'cloud':cloud.get('overall_status'),'threecommas':(cloud.get('threecommas') or {}).get('status'),'main_app':(cloud.get('main_app') or {}).get('status'),'publication':(cloud.get('publication') or {}).get('status'),'diagnostics':health.get('diagnostics_state'),'score':health.get('diagnostics_score')},
      'next_steps':[x for x in [
        'Review the recommended DCA settings in the Bots workspace.' if top.get('bot_name') else None,
        'Confirm available quote-currency capital before deployment.' if can_fund is not True else None,
        'Resolve missing DCA fields before making changes.' if missing else None,
        'Apply changes manually in 3Commas only after approval.'
      ] if x],
    }
    payload['snapshot_id']=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:24]
    return payload

def main():
    OUTPUT.write_text(json.dumps(build(),indent=2),encoding='utf-8')
    print(f'Adaptive decision workspace written: {OUTPUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
