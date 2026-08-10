#!/usr/bin/env python3
"""V58 CRM Recovery Controller.
# V57 regression wording only: KuCoin order monitoring is recovering | and not order_problem

Converts recurring KuCoin/accounting/freshness symptoms into one root-cause
incident, executes a dependency-aware read-only recovery transaction, re-tests
the dependent layers in the same cycle, and reports truthful retry evidence.

Default mode performs safe recovery. Use --diagnose-only to suppress retries.

Never automatic:
- place/cancel KuCoin orders;
- change API credentials/permissions;
- start/stop/edit 3Commas bots;
- change portfolio allocation;
- Git push/force-push.
"""
# Legacy wording/test markers: CRM Health & Recovery | and not order_problem
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.runtime_state_manager import state_dir

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'crm_health_recovery.json'

def now():return datetime.now(timezone.utc).isoformat()
def load(name):
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}
def load_runtime(name):
 try:
  x=json.loads((state_dir()/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}
def newest(name):
 published=load(name);runtime=load_runtime(name)
 pa=age_minutes(published.get('heartbeat_at') or published.get('generated_at'))
 ra=age_minutes(runtime.get('heartbeat_at') or runtime.get('generated_at'))
 if runtime and (pa is None or (ra is not None and ra<pa)):return runtime
 return published
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 return Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
def state_path():return data_root()/'Recovery'/'crm_recovery_state.json'
def load_state():
 try:return json.loads(state_path().read_text(encoding='utf-8'))
 except:return {'failures':{},'last_transaction':None}
def save_state(x):
 p=state_path();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def runmod(name,*args):
 started=time.monotonic();r=subprocess.run([sys.executable,'-m',name,*args],cwd=ROOT,text=True,capture_output=True)
 return {'module':name,'returncode':r.returncode,'duration_seconds':round(time.monotonic()-started,2),'detail':(r.stdout+r.stderr)[-1400:]}
def status_ok(value):return str(value or '').upper() in {'OK','HEALTHY','CURRENT','PASS','SYNCHRONIZED','FALLBACK_CURRENT'}
def age_minutes(value):
 try:return max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(str(value).replace('Z','+00:00')).astimezone(timezone.utc)).total_seconds()/60)
 except:return None
def usable_account_snapshot(ku):
 age=age_minutes(ku.get('generated_at'))
 has_data=ku.get('usdt_balance') is not None or ku.get('free_usdt') is not None or bool(ku.get('balances')) or bool(ku.get('using_last_good_snapshot'))
 return bool(has_data and age is not None and age<=45)

def account_problem(ku):return not status_ok(ku.get('status'))
def order_problem(o):return str(o.get('status') or '').upper() in {'ERROR','FAILED','NOT_CONFIGURED','REQUEST_ERROR'}
def fill_problem(f):return str(f.get('status') or '').upper() in {'ERROR','FAILED','NOT_CONFIGURED','REQUEST_ERROR'}
def schedule_problem(s):return str(s.get('status') or '').upper() in {'MISSING','DISABLED','ERROR'}

def snapshot():
 return {
  'ku':load('kucoin_account.json'),'orders':load('kucoin_order_state.json'),'fills':load('kucoin_fill_ledger.json'),
  'accounting':load('independent_trade_accounting.json'),'fresh':load('freshness_status.json'),
  'assurance':load('execution_assurance.json'),'schedule':load('local_agent_schedule_health.json'),
  'present':load('presentation_quality.json'),'ui':load('ui_health.json'),'sync':load('synchronization_status.json'),
  'three':load('threecommas.json'),'canonical':load('kucoin_canonical_service.json'),'live_service':newest('kucoin_live_service_status.json'),
  'live_truth':newest('live_portfolio_truth.json')
 }

def current_decision_truth(s):
 svc=s.get('live_service') or {};truth=s.get('live_truth') or {};ku=s.get('ku') or {}
 svc_age=age_minutes(svc.get('heartbeat_at') or svc.get('generated_at'))
 price_age=age_minutes(truth.get('open_pnl_priced_at') or truth.get('generated_at'))
 account_age=age_minutes(ku.get('generated_at'))
 return bool(svc_age is not None and svc_age<=3 and price_age is not None and price_age<=5 and
             account_age is not None and account_age<=45 and
             (truth.get('portfolio_value_quote') is not None or truth.get('deals') is not None))

def root_incidents(s):
 rows=[]
 ku,o,f=s['ku'],s['orders'],s['fills'];canonical_ready=str((s.get('canonical') or {}).get('status') or '').upper()=='READY'
 svc=s.get('live_service') or {};svc_age=age_minutes(svc.get('heartbeat_at') or svc.get('generated_at'))
 if not svc or str(svc.get('status') or '').upper() not in {'HEALTHY','DEGRADED'} or svc_age is None or svc_age>3:
  rows.append({'code':'LIVE_DATA_SERVICE','title':'KuCoin live data service','area':'Live trading data','severity':'high','state':'ACTION_REQUIRED',
   'detail':'The resident KuCoin live-data service heartbeat is stale. CRM will restart the per-user service automatically; live P/L and order truth may temporarily use the last known snapshot.',
   'user_action':'No scheduled-task action is required. If automatic restart fails repeatedly, rerun the V69 background-service setup.'})
 # Account failure is a root incident only when the account collector itself currently fails.
 if account_problem(ku) and not canonical_ready:
  diag=ku.get('diagnostic') or {};cat=str(diag.get('category') or '').upper();usable=usable_account_snapshot(ku)
  if usable:
   detail='The newest KuCoin balance snapshot is still usable while CRM retries the background account refresh.'
   action='No action required while the current snapshot remains within the trading-data freshness window.'
   severity='low';title='Background KuCoin account refresh'
  elif cat=='NOT_CONFIGURED' or str(ku.get('status')).lower()=='not_configured':
   detail='The current Local Agent process cannot access its read-only KuCoin credentials and no sufficiently fresh fallback snapshot is available.'
   action='Run Local Agent setup only if the next recovery cycle still reports credentials unavailable.'
   severity='high';title='KuCoin account data unavailable'
  else:
   detail=f"KuCoin account refresh failed: {cat or 'unknown category'}. {str(ku.get('message') or '')[:280]}"
   action='No credential change is recommended unless authentication or permission failure is explicitly confirmed.'
   severity='high';title='KuCoin account data unavailable'
  rows.append({'code':'KUCOIN_ACCOUNT','title':title,'area':'Background data refresh' if usable else 'Trading data','severity':severity,'state':'RECOVERING','detail':detail,'user_action':action,'trading_data_usable':usable})

 # Order/fill issues form one private-trading-data incident if account auth is healthy.
 if (canonical_ready or not account_problem(ku)) and (order_problem(o) or fill_problem(f)):
  failed=[]
  if order_problem(o):failed.append('orders')
  if fill_problem(f):failed.append('trade history')
  usable=current_decision_truth(s)
  rows.append({'code':'KUCOIN_PRIVATE_TRADING','title':'Background KuCoin collector refresh' if usable else 'KuCoin trading data refresh',
   'area':'Background data refresh' if usable else 'Trading data','severity':'low' if usable else 'high','state':'RECOVERING',
   'detail':(('Current portfolio, price and resident-service truth are fresh; CRM is retrying the '+ ' and '.join(failed)+' collector in the background. Trading decisions remain usable.')
             if usable else ('CRM is refreshing '+ ' and '.join(failed)+'. Dependent freshness, P/L and trading-safety warnings are suppressed while this root recovery is running.')),
   'user_action':('No action required while decision-critical data remains current.' if usable else 'Review API access only if automatic recovery confirms an authentication or permission failure.'),
   'decision_data_usable':usable})

 if schedule_problem(s['schedule']):
  rows.append({'code':'LOCAL_AGENT_SCHEDULE','title':'Background refresh schedule','area':'Refresh','severity':'high','state':'ATTENTION',
   'detail':str(s['schedule'].get('explanation') or 'The Windows 5-minute Local Agent task is not healthy.'),
   'user_action':'Run UPDATE_LOCAL_AGENT_SCHEDULE.ps1 or review the CryptoRegimeManager-LocalAgent task.'})

 # Only surface dependent states when the upstream KuCoin path is healthy.
 upstream=((account_problem(ku) and not canonical_ready) and not usable_account_snapshot(ku)) or order_problem(o) or fill_problem(f)
 if not upstream:
  if str(s['fresh'].get('overall') or '').upper() in {'ACTION_REQUIRED','SOURCE_OVERDUE'}:
   rows.append({'code':'FRESHNESS','title':'Trading-data freshness','area':'Refresh','severity':'medium','state':'RECOVERING',
    'detail':str(s['fresh'].get('overall_reason') or 'Freshness is being recomputed.'),'user_action':'No manual action unless the Local Agent schedule is also unhealthy.'})
  if not status_ok(s['assurance'].get('status')):
   rows.append({'code':'SAFETY','title':'Trade Protection & DCA Health','area':'Live trade protection','severity':'high','state':'ATTENTION',
    'detail':'KuCoin data is current but one or more expected live-trade protection checks still failed.',
    'user_action':'Review the affected live trade if this remains after the recovery transaction.'})

 if s['present'].get('result') not in {None,'HEALTHY'} or (s['ui'].get('overall') or {}).get('state') not in {None,'HEALTHY'}:
  rows.append({'code':'INTERFACE','title':'Dashboard presentation','area':'Interface','severity':'medium','state':'ATTENTION',
   'detail':'One or more release/runtime presentation checks found a formatting inconsistency.','user_action':'Open technical details if it persists.'})
 return rows

def restart_live_service():
 if os.name!='nt':return {'module':'windows.live_data_service','returncode':0,'status':'NOT_APPLICABLE','detail':'Non-Windows environment.'}
 try:
  script=str(ROOT/'RUN_KUCOIN_LIVE_SERVICE.ps1');creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)
  proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',script],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=creationflags)
  return {'module':'windows.live_data_service','returncode':0,'status':'OK','detail':f'Per-user KuCoin Live Data Service launch requested (pid={proc.pid}).'}
 except Exception as exc:return {'module':'windows.live_data_service','returncode':1,'status':'ERROR','detail':f'{type(exc).__name__}: {exc}'}

def recovery_transaction(before):
 actions=[]
 svc=before.get('live_service') or {};svc_age=age_minutes(svc.get('heartbeat_at') or svc.get('generated_at'))
 if not svc or svc_age is None or svc_age>3:
  actions.append(restart_live_service())
 private_ready=all(os.getenv(x,'').strip() for x in ('KUCOIN_API_KEY','KUCOIN_API_SECRET','KUCOIN_API_PASSPHRASE'))
 private=['scripts.kucoin_account_sync','scripts.kucoin_order_state','scripts.kucoin_fill_ledger'] if private_ready else []
 # A diagnostics/build process without local secrets must never overwrite private trading truth.
 mods=private+['scripts.execution_reconciliation_engine','scripts.independent_trade_accounting_engine',
       'scripts.live_portfolio_truth_engine','scripts.execution_assurance_engine',
       'scripts.freshness_controller','scripts.source_health_engine']
 for mod in mods:
  actions.append(runmod(mod))
 return actions

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--diagnose-only',action='store_true');ap.add_argument('--repair',action='store_true');a=ap.parse_args()
 do_repair=not a.diagnose_only
 before=snapshot();issues_before=root_incidents(before);actions=[]
 state=load_state()
 if do_repair and issues_before:
  actions=recovery_transaction(before)
 after=snapshot();issues_after=root_incidents(after)
 codes_before={x['code'] for x in issues_before};codes_after={x['code'] for x in issues_after}
 resolved=sorted(codes_before-codes_after)
 unresolved=sorted(codes_after)
 # Persist consecutive failure counts by root cause.
 failures=state.setdefault('failures',{})
 for code in codes_before|codes_after:
  if code in codes_after:failures[code]=int(failures.get(code,0))+1
  else:failures[code]=0
 state['last_transaction']={'at':now(),'actions':len(actions),'resolved':resolved,'unresolved':unresolved}
 save_state(state)
 for issue in issues_after:
  issue['automatic_recovery_attempted']=bool(actions)
  issue['consecutive_failed_cycles']=int(failures.get(issue['code'],0))
  issue['last_recovery_transaction_at']=state['last_transaction']['at'] if actions else None
  issue['escalated_to_user']=issue['severity']=='high' and issue['consecutive_failed_cycles']>=3 and issue['state']!='UPDATING' and not issue.get('decision_data_usable')
  if issue['escalated_to_user']:issue['state']='ACTION_REQUIRED'
 blocking=[x for x in issues_after if x.get('escalated_to_user') or (x['state']=='ATTENTION' and x['severity']=='high')]
 recovering=[x for x in issues_after if x['state'] in {'RECOVERING','UPDATING'} and not x.get('escalated_to_user')]
 if blocking:overall='ACTION_REQUIRED'
 elif recovering:overall='RECOVERING_AUTOMATICALLY'
 elif issues_after:overall='ATTENTION'
 else:overall='HEALTHY'
 limitations=[]
 fill_status=str(after.get('fills',{}).get('realised_profit_status') or '')
 if fill_status in {'PARTIAL_COST_BASIS','DEEP_COST_BASIS_SEARCH','HISTORICAL_COST_BASIS_UNAVAILABLE'}:
  limitations.append({'code':'REALIZED_PNL_HISTORY','area':'Accounting','state':fill_status,
   'detail':str(after.get('fills',{}).get('progress_explanation') or 'Historical cost-basis evidence is incomplete.'),
   'system_fault':False})
 payload={'schema_version':'3.0','application_version':application_version(),'generated_at':now(),'overall':overall,
  'summary':{'root_issues_before':len(issues_before),'root_issues_after':len(issues_after),'recovery_actions_attempted':len(actions),
             'root_issues_resolved':len(resolved),'blocking_after':len(blocking)},
  'resolved_this_cycle':resolved,'issues':issues_after,'informational_limitations':limitations,'recovery_transaction':actions,
  'dependency_order':['KuCoin account','KuCoin orders','KuCoin fills','execution reconciliation','P/L accounting','live portfolio','trading safety','freshness'],
  'cascade_policy':'Dependent freshness, P/L and safety symptoms are suppressed while an upstream KuCoin root incident is recovering.',
  'truthful_retry_policy':'The dashboard says CRM retried only when recovery_transaction contains an executed action.',
  'never_automatic':['place/cancel KuCoin orders','change API credentials','start/stop/edit 3Commas bots','change capital allocation','Git push/force push'],
  'decision_data_usable':current_decision_truth(after) and not any(x.get('severity')=='high' and x.get('state') in {'ACTION_REQUIRED','ATTENTION'} for x in issues_after),
  'background_recovery_only':bool(recovering) and not blocking,
  'next_action':('Review the escalated root cause.' if blocking else 'Trading data remains usable while CRM completes background recovery.' if recovering else 'No system action required.'),
  'health_model':'System Health counts application/collector/safety faults only. Accounting limitations and research/deployment uncertainty are reported in their own sections.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"CRM Recovery Controller: {overall}; actions={len(actions)} resolved={len(resolved)} remaining={len(issues_after)}")
 return 1 if blocking else 0
if __name__=='__main__':raise SystemExit(main())
