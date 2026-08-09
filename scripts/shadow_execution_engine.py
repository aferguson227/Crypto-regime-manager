#!/usr/bin/env python3
"""V51 shadow execution plans. Generates hypothetical order ladders only."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'shadow_execution_plans.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def main():
 review=load('candidate_review.json');alloc=load('portfolio_allocation_recommendations.json');aby={str(x.get('asset') or '').upper():x for x in alloc.get('recommendations') or []};rows=[]
 for x in review.get('candidates') or []:
  if float(x.get('readiness_pct') or 0)<100:continue
  a=str(x.get('asset') or '').upper();settings=x.get('settings') or {};al=aby.get(a) or {};budget=num(al.get('recommended_allocation_usdt'))
  n=int(settings.get('safety_orders') or 0);vs=num(settings.get('volume_scale')) or 1;weights=[1]+[vs**i for i in range(n)];unit=(budget/sum(weights)) if budget and sum(weights)>0 else None
  orders=[]
  if unit is not None:
   orders.append({'role':'BASE_ORDER','notional_usdt':round(unit,2)})
   for i in range(n):orders.append({'role':f'SAFETY_ORDER_{i+1}','notional_usdt':round(unit*(vs**i),2)})
  rows.append({'asset':a,'pair':x.get('pair'),'current_regime':x.get('current_regime'),'entry_trigger':x.get('entry_trigger'),'settings':settings,'allocated_budget_usdt':budget,
    'hypothetical_order_ladder':orders,'checks':['candidate readiness = 100%','portfolio slot/allocation available' if budget is not None else 'allocation unavailable','manual confirmation required'],
    'status':'SHADOW_READY' if budget is not None else 'WAITING_FOR_ALLOCATION'})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'SHADOW_ONLY','plans':rows,
  'live_order_endpoints_called':False,'automatic_execution':False,'purpose':'Compare CRM intended DCA/order behaviour with 3Commas before enabling any future direct execution.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Shadow execution plans written: {OUT}; plans={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
