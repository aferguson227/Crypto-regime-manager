#!/usr/bin/env python3
"""V52 native KuCoin execution-readiness gate. No trading calls are made."""
from __future__ import annotations
import json,os,re,uuid
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'native_execution_readiness.json';POL=ROOT/'config'/'v52_execution_assurance_policy.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def loadp():
 try:return json.loads(POL.read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 p=loadp();cfg=p.get('native_execution') or {};assure=load('execution_assurance.json');shadow=load('shadow_execution_plans.json');ku=load('kucoin_account.json');orders=load('kucoin_order_state.json')
 spot_enabled=os.getenv('CRM_KUCOIN_SPOT_TRADING_CONFIRMED','').strip().lower() in {'1','true','yes'}
 feature=os.getenv(str(cfg.get('feature_flag') or 'CRM_NATIVE_EXECUTION_ENABLE'),'').strip().lower() in {'1','true','yes'}
 kill=os.getenv(str(cfg.get('kill_switch_env') or 'CRM_EXECUTION_KILL_SWITCH'),'1').strip().lower() not in {'0','false','off','no'}
 plans=[]
 for x in shadow.get('plans') or []:
  oid=f"{cfg.get('client_oid_prefix','crm52')}-{str(x.get('asset') or '').lower()}-{uuid.uuid4().hex[:18]}"
  plans.append({'asset':x.get('asset'),'pair':x.get('pair'),'shadow_status':x.get('status'),'client_oid_example':oid,
    'planned_budget_usdt':x.get('allocated_budget_usdt'),'hypothetical_order_count':len(x.get('hypothetical_order_ladder') or []),
    'idempotency_method':'Unique CRM clientOid per intended order; retries must query by clientOid before any future live submission.'})
 checks=[
  {'label':'KuCoin private read access','state':'PASS' if str(ku.get('status')).upper()=='OK' else 'PENDING','detail':'Required for balances/account truth.'},
  {'label':'KuCoin order-state visibility','state':'PASS' if str(orders.get('status')).upper()=='OK' else 'PENDING','detail':'Required to confirm active/done order state.'},
  {'label':'Execution assurance','state':'PASS' if assure.get('status')=='HEALTHY' else 'PENDING','detail':'Order protection/provider reconciliation must be healthy.'},
  {'label':'Shadow plans available','state':'PASS' if plans else 'PENDING','detail':f'{len(plans)} candidate shadow plan(s) available.'},
  {'label':'Spot trading permission explicitly confirmed','state':'PASS' if spot_enabled else 'LOCKED','detail':'V52 never infers Spot trading permission from read-only access.'},
  {'label':'Native execution feature flag','state':'LOCKED' if not feature else 'REQUESTED','detail':'V52 keeps all live order code paths disabled.'},
  {'label':'Kill switch','state':'PASS' if kill else 'FAIL','detail':'Kill switch must remain ON in V52.'}
 ]
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'LOCKED_SHADOW',
  'overall':'SHADOW_READY' if all(x['state']=='PASS' for x in checks[:4]) else 'BUILDING',
  'checks':checks,'shadow_plans':plans,'verified_api_contract':{
    'place_order':cfg.get('direct_order_endpoint'),'place_order_sync':cfg.get('sync_order_endpoint'),
    'get_by_client_oid':cfg.get('get_order_by_client_oid'),'cancel_by_client_oid':cfg.get('cancel_by_client_oid'),
    'required_permission':cfg.get('required_permission'),'withdrawal_permission_required':False},
  'live_order_submission_implemented':False,'automatic_execution':False,
  'next_phase':'Guarded manual native execution can be enabled only in a later release after shadow parity and restart-recovery tests pass.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Native execution readiness: {payload["overall"]}; live writes locked');return 0
if __name__=='__main__':raise SystemExit(main())
