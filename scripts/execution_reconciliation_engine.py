#!/usr/bin/env python3
"""V51 KuCoin ↔ 3Commas deal reconciliation and stale-provider detection."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'execution_reconciliation.json';POL=ROOT/'config'/'v51_execution_policy.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def dt(v):
 try:
  if isinstance(v,(int,float)):
   x=float(v);x=x/1000 if x>1e12 else x
   return datetime.fromtimestamp(x,tz=timezone.utc)
  return datetime.fromisoformat(str(v).replace('Z','+00:00'))
 except:return None
def main():
 tc=load('threecommas.json');fills=load('kucoin_fill_ledger.json');orders=load('kucoin_order_state.json');pol=load('v51_execution_policy.json') if False else {}
 try:policy=json.loads(POL.read_text(encoding='utf-8-sig'))
 except:policy={}
 ratio=float((policy.get('reconciliation') or {}).get('closed_fill_quantity_ratio',.9));now=datetime.now(timezone.utc)
 fillrows=(fills.get('reconciliation') or {}).get('raw_fills') or []
 # Fallback: the ledger snapshot intentionally does not publish raw fills; use its per-asset sell reconciliation plus recent closed orders.
 closed=orders.get('recent_closed_orders') or [];active=orders.get('active_orders') or [];rows=[]
 for asset,bucket in (tc.get('assets') or {}).items():
  a=str(asset).upper()
  for d in bucket.get('deals') or []:
   opened=dt(d.get('created_at'));qty=num(d.get('allocated_asset_quantity'));provider_open=str(d.get('status') or '').lower() not in {'closed','completed','cancelled','finished'}
   sell_orders=[]
   for o in closed:
    sym=str(o.get('symbol') or '').upper();side=str(o.get('side') or '').lower();created=dt(o.get('createdAt') or o.get('created_at') or o.get('createdTime'))
    if sym==f'{a}-USDT' and side=='sell' and (not opened or not created or created>=opened):
     sell_orders.append(o)
   open_orders=[o for o in active if str(o.get('symbol') or '').upper()==f'{a}-USDT']
   # Use order filled size/funds if present. Strong closure only when a recent completed sell covers most allocated quantity.
   sold=max([num(o.get('dealSize') or o.get('filledSize') or o.get('size')) or 0 for o in sell_orders] or [0])
   exchange_closed=bool(provider_open and qty and sold>=qty*ratio and not open_orders)
   close_time=None
   if exchange_closed:
    latest=max(sell_orders,key=lambda x:str(x.get('updatedAt') or x.get('createdAt') or x.get('created_at') or ''))
    raw=latest.get('updatedAt') or latest.get('createdAt') or latest.get('created_at');close_time=str(raw) if raw is not None else None
   age_min=None
   if exchange_closed and opened:
    # Conservative mismatch age uses newest exchange snapshot age when exact close timestamp format is unavailable.
    gen=dt(orders.get('generated_at'));age_min=round((now-gen).total_seconds()/60,1) if gen else None
   state='PROVIDER_STALE_OPEN' if exchange_closed else ('PROVIDER_OPEN_EXCHANGE_UNCONFIRMED' if provider_open else 'CONSISTENT')
   rows.append({'asset':a,'bot_id':d.get('bot_id'),'bot_name':d.get('bot_name'),'provider':'3Commas','provider_deal_status':d.get('status'),
    'provider_reports_open':provider_open,'kucoin_recent_sell_orders':len(sell_orders),'kucoin_active_orders':len(open_orders),'allocated_quantity':qty,
    'largest_recent_completed_sell_quantity':sold,'exchange_closed_evidence':exchange_closed,'exchange_close_evidence_time':close_time,
    'reconciliation_state':state,'blocked_next_entry_risk':bool(exchange_closed and provider_open),
    'crm_position_truth':'CLOSED' if exchange_closed else ('OPEN' if provider_open else 'CLOSED_OR_INACTIVE'),
    'action':'Reconcile/cancel stale 3Commas deal before relying on provider for the next entry.' if exchange_closed else 'No stale-provider closure proven.',
    'read_only':True})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now.isoformat(),'authority':'KuCoin exchange order/fill evidence overrides stale execution-provider telemetry when closure is proven.',
  'deals':rows,'summary':{'provider_open_deals':sum(x['provider_reports_open'] for x in rows),'proven_stale_open_deals':sum(x['reconciliation_state']=='PROVIDER_STALE_OPEN' for x in rows),
  'blocked_next_entry_risks':sum(x['blocked_next_entry_risk'] for x in rows)},'write_actions':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Execution reconciliation written: {OUT}; stale={payload["summary"]["proven_stale_open_deals"]}');return 0
if __name__=='__main__':raise SystemExit(main())
