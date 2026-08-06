#!/usr/bin/env python3
"""Build a task-oriented daily trading workspace from canonical command state."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUTPUT=DOCS/'professional_workspace.json'

def load(name):
    try:
        v=json.loads((DOCS/name).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
    except Exception:return {}

def build():
    c=load('command_state.json'); previous=load('professional_workspace.json')
    queue=c.get('priority_queue') or []; recs=c.get('recommendations') or []
    top=queue[0] if queue else {}
    rec=next((r for r in recs if r.get('bot_name')==top.get('bot_name')),recs[0] if recs else {})
    comp=rec.get('production_comparison') or {}; recommended=(comp.get('recommended_settings') or {}).get('values') or {}
    live={d.get('field'):d.get('live_value') for d in comp.get('differences') or []}
    production={d.get('field'):d.get('production_value') for d in comp.get('differences') or []}
    changed=[]
    old=(previous.get('daily_decision') or {}) if isinstance(previous,dict) else {}
    for key,label in [('bot_name','Bot'),('action','Action'),('confidence_pct','Confidence')]:
        before=old.get(key); after=top.get(key)
        if before is not None and before!=after: changed.append({'field':label,'before':before,'after':after})
    for key,val in recommended.items():
        oldv=(previous.get('recommended_settings') or {}).get(key) if isinstance(previous,dict) else None
        if oldv is not None and oldv!=val: changed.append({'field':key,'before':oldv,'after':val})
    cap=c.get('capital') or {}; cloud=c.get('cloud') or {}; health=c.get('health') or {}
    payload={
      'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'read_only':True,'manual_approval_required':True,
      'daily_decision':{'bot_name':top.get('bot_name'),'asset':top.get('asset'),'action':top.get('action'),'confidence_pct':top.get('confidence_pct'),'urgency':top.get('urgency'),'why':list(top.get('rationale') or []),'blockers':list(top.get('blockers') or [])},
      'allocation':{'required_quote':top.get('capital_required') or cap.get('next_required'),'quote_currency':cap.get('currency') or 'USDT','can_fund':top.get('can_fund'),'deployable_quote':cap.get('deployable'),'asset_allocations':cap.get('asset_allocations') or []},
      'recommended_settings':recommended,'live_settings':live,'production_settings':production,'setting_differences':comp.get('differences') or [],
      'what_changed':changed,'risks':c.get('risks') or [],'market':c.get('market') or {},'portfolio':c.get('portfolio') or {},
      'deployment_health':{'cloud':cloud.get('overall_status'),'threecommas':(cloud.get('threecommas') or {}).get('status'),'main_app':(cloud.get('main_app') or {}).get('status'),'publication':(cloud.get('publication') or {}).get('status'),'diagnostics':health.get('diagnostics_state'),'score':health.get('diagnostics_score')},
    }
    seed=json.dumps(payload,sort_keys=True,default=str); payload['snapshot_id']=hashlib.sha256(seed.encode()).hexdigest()[:24]
    return payload
def main():
    OUTPUT.write_text(json.dumps(build(),indent=2),encoding='utf-8'); print(f'Professional workspace written: {OUTPUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
