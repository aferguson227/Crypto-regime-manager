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

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'crm_health_recovery.json'

def now():return datetime.now(timezone.utc).isoformat()
def load(name):
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}
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
def status_ok(value):return str(value or '').upper() in {'OK','HEALTHY','CURRENT','PASS','SYNCHRONIZED'}
def account_problem(ku):return not status_ok(ku.get('status'))
def order_problem(o):return not status_ok(o.get('status'))
def fill_problem(f):return not status_ok(f.get('status'))
def schedule_problem(s):return str(s.get('status') or '').upper() in {'MISSING','DISABLED','ERROR'}

def snapshot():
 return {
  'ku':load('kucoin_account.json'),'orders':load('kucoin_order_state.json'),'fills':load('kucoin_fill_ledger.json'),
  'accounting':load('independent_trade_accounting.json'),'fresh':load('freshness_status.json'),
  'assurance':load('execution_assurance.json'),'schedule':load('local_agent_schedule_health.json'),
  'present':load('presentation_quality.json'),'ui':load('ui_health.json'),'sync':load('synchronization_status.json'),
  'three':load('threecommas.json')
 }

def root_incidents(s):
 rows=[]
 ku,o,f=s['ku'],s['orders'],s['fills']
 # Account failure is a root incident only when the account collector itself currently fails.
 if account_problem(ku):
  diag=ku.get('diagnostic') or {}
  cat=str(diag.get('category') or '').upper()
  # Don't tell the user to add credentials unless the collector specifically proved they are absent.
  if cat=='NOT_CONFIGURED' or str(ku.get('status')).lower()=='not_configured':
   detail='CRM cannot see its local read-only KuCoin credentials in this Local Agent process.'
   action='Run the Local Agent setup again only if the next automatic recovery still reports credentials unavailable.'
  else:
   detail=f"KuCoin account refresh failed: {cat or 'unknown category'}. {str(ku.get('message') or '')[:280]}"
   action='No credential change is recommended unless the diagnostic specifically reports authentication/permission failure.'
  rows.append({'code':'KUCOIN_ACCOUNT','title':'KuCoin account refresh','area':'Trading data','severity':'high','state':'RECOVERING','detail':detail,'user_action':action})

 # Order/fill issues form one private-trading-data incident if account auth is healthy.
 if not account_problem(ku) and (order_problem(o) or fill_problem(f)):
  failed=[]
  if order_problem(o):failed.append('orders')
  if fill_problem(f):failed.append('trade history')
  rows.append({'code':'KUCOIN_PRIVATE_TRADING','title':'KuCoin trading data refresh','area':'Trading data','severity':'high','state':'RECOVERING',
   'detail':'CRM is refreshing '+ ' and '.join(failed)+'. Dependent freshness, P/L and trading-safety warnings are suppressed while this root recovery is running.',
   'user_action':'No action is normally required during automatic recovery. Review API access only after repeated failed recovery transactions.'})

 if schedule_problem(s['schedule']):
  rows.append({'code':'LOCAL_AGENT_SCHEDULE','title':'Background refresh schedule','area':'Refresh','severity':'high','state':'ATTENTION',
   'detail':str(s['schedule'].get('explanation') or 'The Windows 15-minute Local Agent task is not healthy.'),
   'user_action':'Run UPDATE_LOCAL_AGENT_SCHEDULE.ps1 or review the CryptoRegimeManager-LocalAgent task.'})

 # Only surface dependent states when the upstream KuCoin path is healthy.
 upstream=account_problem(ku) or order_problem(o) or fill_problem(f)
 if not upstream:
  if s['accounting'].get('realised_profit_quote') is None:
   rows.append({'code':'PNL_RECONCILIATION','title':'Realised P/L reconciliation','area':'Profit & loss','severity':'low','state':'UPDATING',
    'detail':str(f.get('progress_explanation') or 'CRM is reconciling closed KuCoin fills.'),'user_action':'No manual action required.'})
  if str(s['fresh'].get('overall') or '').upper() in {'ACTION_REQUIRED','SOURCE_OVERDUE'}:
   rows.append({'code':'FRESHNESS','title':'Trading-data freshness','area':'Refresh','severity':'medium','state':'RECOVERING',
    'detail':str(s['fresh'].get('overall_reason') or 'Freshness is being recomputed.'),'user_action':'No manual action unless the Local Agent schedule is also unhealthy.'})
  if not status_ok(s['assurance'].get('status')):
   rows.append({'code':'SAFETY','title':'Trading safety verification','area':'Trading safety','severity':'high','state':'ATTENTION',
    'detail':'KuCoin data is current but one or more expected live-trade protection checks still failed.',
    'user_action':'Review the affected live trade if this remains after the recovery transaction.'})

 if s['present'].get('result') not in {None,'HEALTHY'} or (s['ui'].get('overall') or {}).get('state') not in {None,'HEALTHY'}:
  rows.append({'code':'INTERFACE','title':'Dashboard presentation','area':'Interface','severity':'medium','state':'ATTENTION',
   'detail':'One or more release/runtime presentation checks found a formatting inconsistency.','user_action':'Open technical details if it persists.'})
 return rows

def recovery_transaction(before):
 actions=[]
 # Dependency order is intentional.
 mods=['scripts.kucoin_account_sync','scripts.kucoin_order_state','scripts.kucoin_fill_ledger',
       'scripts.execution_reconciliation_engine','scripts.independent_trade_accounting_engine',
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
  issue['escalated_to_user']=issue['severity']=='high' and issue['consecutive_failed_cycles']>=3 and issue['state']!='UPDATING'
  if issue['escalated_to_user']:issue['state']='ACTION_REQUIRED'
 blocking=[x for x in issues_after if x.get('escalated_to_user') or (x['state']=='ATTENTION' and x['severity']=='high')]
 recovering=[x for x in issues_after if x['state'] in {'RECOVERING','UPDATING'} and not x.get('escalated_to_user')]
 if blocking:overall='ACTION_REQUIRED'
 elif recovering:overall='RECOVERING_AUTOMATICALLY'
 elif issues_after:overall='ATTENTION'
 else:overall='HEALTHY'
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now(),'overall':overall,
  'summary':{'root_issues_before':len(issues_before),'root_issues_after':len(issues_after),'recovery_actions_attempted':len(actions),
             'root_issues_resolved':len(resolved),'blocking_after':len(blocking)},
  'resolved_this_cycle':resolved,'issues':issues_after,'recovery_transaction':actions,
  'dependency_order':['KuCoin account','KuCoin orders','KuCoin fills','execution reconciliation','P/L accounting','live portfolio','trading safety','freshness'],
  'cascade_policy':'Dependent freshness, P/L and safety symptoms are suppressed while an upstream KuCoin root incident is recovering.',
  'truthful_retry_policy':'The dashboard says CRM retried only when recovery_transaction contains an executed action.',
  'never_automatic':['place/cancel KuCoin orders','change API credentials','start/stop/edit 3Commas bots','change capital allocation','Git push/force push'],
  'next_action':('Review the escalated root cause.' if blocking else 'No manual action required while CRM is recovering.' if recovering else 'No manual action required.')}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"CRM Recovery Controller: {overall}; actions={len(actions)} resolved={len(resolved)} remaining={len(issues_after)}")
 return 1 if blocking else 0
if __name__=='__main__':raise SystemExit(main())
