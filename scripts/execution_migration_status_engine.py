#!/usr/bin/env python3
"""V54 migration status from 3Commas-dependent execution to CRM-managed KuCoin execution.

Advisory only. No live order endpoint is called.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'execution_migration_status.json'

def load(n):
 try:
  x=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}

def main():
 ku=load('kucoin_account.json');orders=load('kucoin_order_state.json');fills=load('kucoin_fill_ledger.json')
 assurance=load('execution_assurance.json');native=load('native_execution_readiness.json');shadow=load('shadow_execution_plans.json')
 recon=load('execution_reconciliation.json');truth=load('live_portfolio_truth.json')

 stages=[
  {'id':'ACCOUNT_READ','label':'KuCoin balances','complete':str(ku.get('status') or '').upper()=='OK','detail':'CRM can read KuCoin balances/capital directly.'},
  {'id':'ORDER_READ','label':'KuCoin orders','complete':str(orders.get('status') or '').upper()=='OK','detail':'CRM can independently see open and completed KuCoin orders.'},
  {'id':'FILL_LEDGER','label':'KuCoin trade history','complete':str(fills.get('status') or '').upper()=='OK','detail':'CRM can persist fills and reconstruct realised P/L independently.'},
  {'id':'PROTECTION_CHECKS','label':'Trade protection checks','complete':assurance.get('status')=='HEALTHY','detail':'CRM verifies TP/safety-order integrity against KuCoin.'},
  {'id':'SHADOW_PLANS','label':'CRM test trading plans','complete':bool(shadow.get('plans')),'detail':'CRM can generate the intended DCA/order ladder without placing it.'},
  {'id':'RESTART_RECOVERY','label':'Restart-safe order identity','complete':bool((native.get('shadow_plans') or [])),'detail':'Deterministic client order identity is available for future idempotent execution.'},
  {'id':'GUARDED_LIVE','label':'Guarded direct trading','complete':False,'detail':'Deliberately locked in V54. Requires successful shadow parity and explicit later release approval.'}
 ]
 complete=sum(x['complete'] for x in stages);pct=round(100*complete/len(stages),1)
 stale=int((recon.get('summary') or {}).get('proven_stale_open_deals') or 0)
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
    'mode':'MIGRATION_IN_PROGRESS','progress_pct':pct,'completed_stages':complete,'total_stages':len(stages),'stages':stages,
    'threecommas_role':'SECONDARY_TRANSITION_PROVIDER',
    'kucoin_role':'AUTHORITATIVE_ACCOUNT_ORDER_FILL_SOURCE',
    'current_live_positions':int(truth.get('effective_open_deal_count') or 0),
    'provider_mismatches':stale,
    'next_required_stage':next((x for x in stages if not x['complete']),None),
    'live_order_submission_enabled':False,
    'message':'CRM is progressively replacing 3Commas operational dependencies. Direct KuCoin trading remains locked until the read/reconciliation/shadow stages are proven reliable.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8')
 print(f'Execution migration status: {pct}% · {complete}/{len(stages)} stages')
 return 0
if __name__=='__main__':raise SystemExit(main())
