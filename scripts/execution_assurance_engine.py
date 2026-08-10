#!/usr/bin/env python3
"""V52 execution assurance / order-integrity engine.
Legacy regression marker: SAFETY_ORDER_LADDER_INCOMPLETE

Compares provider-reported live deals with KuCoin open orders and the CRM expected
shadow ladder. It is read-only and never cancels or places orders.
"""
from __future__ import annotations
import json,math
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'execution_assurance.json';POL=ROOT/'config'/'v52_execution_assurance_policy.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def loadp():
 try:return json.loads(POL.read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def pctdiff(a,b):
 if a in (None,0) or b is None:return None
 return abs(float(a)-float(b))/abs(float(a))*100
def main():
 orders=load('kucoin_order_state.json');recon=load('execution_reconciliation.json');truth=load('live_portfolio_truth.json')
 profiles=load('live_bot_profiles.json');shadow=load('shadow_execution_plans.json');tc=load('threecommas.json');capital=load('capital_intelligence.json');p=loadp();cfg=p.get('execution_assurance') or {}
 active=orders.get('active_orders') or [];closed=orders.get('recent_closed_orders') or [];orders_healthy=str(orders.get('status') or '').upper()=='OK'
 profby={str(x.get('asset') or '').upper():x for x in profiles.get('bots') or []};planby={str(x.get('asset') or '').upper():x for x in shadow.get('plans') or []}
 rows=[]
 assets=set([str(x.get('asset') or '').upper() for x in truth.get('deals') or []]+list((tc.get('assets') or {}).keys()))
 for asset in sorted(a for a in assets if a):
  open_orders=[o for o in active if str(o.get('symbol') or '').upper()==f'{asset}-USDT']
  buys=[o for o in open_orders if str(o.get('side') or '').lower()=='buy'];sells=[o for o in open_orders if str(o.get('side') or '').lower()=='sell']
  td=[x for x in truth.get('deals') or [] if str(x.get('asset') or '').upper()==asset]
  effective_open=any(x.get('effective_position_state')=='OPEN' for x in td)
  stale=any(x.get('provider_stale') for x in td)
  prof=profby.get(asset) or {};live=prof.get('live_settings') or {};plan=planby.get(asset) or {}
  expected_so=int(live.get('safety_orders') or len([x for x in plan.get('hypothetical_order_ladder') or [] if str(x.get('role','')).startswith('SAFETY_ORDER')]) or 0)
  expected_tp=bool(effective_open and cfg.get('require_tp_for_open_position',True))
  issues=[];checks=[]
  checks.append({'check':'Exchange/provider lifecycle reconciliation','state':'FAIL' if stale else 'PASS','detail':'Provider stale open deal is proven closed by KuCoin.' if stale else 'No proven stale-open lifecycle mismatch.'})
  if expected_tp:
   state='PASS' if sells else ('UNVERIFIED' if not orders_healthy else 'FAIL')
   checks.append({'check':'Take-profit order verified','state':state,'detail':(f'{len(sells)} active {asset}/USDT sell order(s) found on KuCoin.' if sells else ('Current KuCoin order collection is incomplete, so CRM cannot yet confirm or deny TP protection.' if not orders_healthy else f'No active {asset}/USDT sell order was found after successful KuCoin order collection.'))})
   if not sells and orders_healthy:issues.append('MISSING_TAKE_PROFIT_PROTECTION')
  else:checks.append({'check':'Take-profit protection present','state':'NOT_REQUIRED','detail':'No exchange-confirmed open position currently requires TP protection.'})
  if effective_open and expected_so:
   reserve=num(capital.get('remaining_active_deal_dca_reserve') or capital.get('active_dca_reserve') or capital.get('reserved_capital'))
   max_active=int(live.get('max_active_safety_orders') or 0)
   if not orders_healthy:
    state='UNVERIFIED';detail='KuCoin order collection is incomplete; DCA order presence cannot be fully verified yet.'
   elif buys:
    state='PASS';detail=f'{len(buys)} live DCA buy order(s) visible on KuCoin. Bot profile allows up to {expected_so} safety orders.'
   else:
    state='READY';detail=f'No DCA buy order is currently resting on KuCoin. The bot remains configured for up to {expected_so} safety orders'+(f' with {max_active} simultaneously active.' if max_active else '.')+' Provider-controlled DCA orders may be staged only when their trigger is reached.'
   checks.append({'check':'DCA order protection','state':state,'detail':detail})
   checks.append({'check':'DCA capital reserve','state':'PASS' if reserve is not None and reserve>=0 else 'UNVERIFIED',
    'detail':(f'{reserve:.2f} USDT is protected for remaining active-trade DCA commitments.' if reserve is not None else 'CRM cannot yet calculate the remaining DCA capital reserve.')})
  else:checks.append({'check':'DCA order protection','state':'NOT_REQUIRED','detail':'No reconciled active position currently requires a DCA ladder.'})
  if not effective_open and open_orders:
   issues.append('ORPHAN_ORDERS_WITHOUT_OPEN_POSITION')
   checks.append({'check':'No leftover orders after a closed trade','state':'FAIL','detail':f'{len(open_orders)} open KuCoin order(s) remain while CRM has no effective open position.'})
  else:checks.append({'check':'No leftover orders after a closed trade','state':'PASS','detail':'No leftover KuCoin orders were detected after a closed trade.'})
  if effective_open and not open_orders and orders_healthy:
   issues.append('OPEN_POSITION_WITH_NO_MANAGEMENT_ORDERS')
  health='FAIL' if any(x.startswith('MISSING_TAKE') or x.startswith('OPEN_POSITION') for x in issues) else ('ATTENTION' if issues else 'HEALTHY')
  rows.append({'asset':asset,'status':health,'effective_open_position':effective_open,'provider_stale':stale,
    'kucoin_active_orders':len(open_orders),'kucoin_active_buy_orders':len(buys),'kucoin_active_sell_orders':len(sells),
    'expected_safety_orders':expected_so,'checks':checks,'issues':issues,
    'next_action':('Do not rely on 3Commas for protection until the missing KuCoin orders are restored or the position is manually reconciled.' if health=='FAIL'
      else 'Review any provider/order mismatch before the next entry.' if health=='ATTENTION' else 'Exchange protection is consistent with the current reconciled state.'),
    'read_only':True})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'status':'FAIL' if any(x['status']=='FAIL' for x in rows) else ('ATTENTION' if any(x['status']=='ATTENTION' for x in rows) else 'HEALTHY'),
  'assets':rows,'summary':{'assets_checked':len(rows),'failed':sum(x['status']=='FAIL' for x in rows),'attention':sum(x['status']=='ATTENTION' for x in rows),
  'orphan_order_assets':sum('ORPHAN_ORDERS_WITHOUT_OPEN_POSITION' in x['issues'] for x in rows),
  'missing_tp_assets':sum('MISSING_TAKE_PROFIT_PROTECTION' in x['issues'] for x in rows)},
  'authority':'KuCoin open/closed order state + CRM reconciled position truth. 3Commas is secondary provider telemetry.','automatic_exchange_writes':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Execution assurance: {payload["status"]}; assets={len(rows)} failures={payload["summary"]["failed"]}');return 0
if __name__=='__main__':raise SystemExit(main())
