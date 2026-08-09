#!/usr/bin/env python3
"""V55 CRM Health & Recovery Engine.

Diagnoses recurring operational/UI issues and applies only low-risk, read-only or
local-regeneration repairs automatically. It never places/cancels exchange orders,
changes API credentials, mutates 3Commas bots, pushes Git, or changes portfolio state.
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'crm_health_recovery.json'

def load(n):
 try:
  x=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}

def runmod(name,*args):
 r=subprocess.run([sys.executable,'-m',name,*args],cwd=ROOT,text=True,capture_output=True)
 return r.returncode,(r.stdout+r.stderr)[-1200:]

def item(code,title,area,severity,state,detail,auto=False,repair=None,user_action=None):
 return {'code':code,'title':title,'area':area,'severity':severity,'state':state,'detail':detail,
         'automatic_repair_available':auto,'repair_module':repair,'user_action':user_action}

def diagnose():
 fresh=load('freshness_status.json');ku=load('kucoin_account.json');orders=load('kucoin_order_state.json')
 fills=load('kucoin_fill_ledger.json');account=load('independent_trade_accounting.json')
 present=load('presentation_quality.json');ui=load('ui_health.json');sync=load('synchronization_status.json')
 agent=load('local_agent_status.json');assure=load('execution_assurance.json');three=load('threecommas.json');schedule=load('local_agent_schedule_health.json')
 rows=[]
 order_problem=str(orders.get('status') or '').upper() not in {'OK','HEALTHY'}
 fill_problem=str(fills.get('status') or '').upper() not in {'OK','HEALTHY'}
 if schedule.get('status') in {'MISSING','DISABLED','ERROR'}:
  rows.append(item('LOCAL_AGENT_SCHEDULE','Background refresh schedule needs attention','Refresh','high','ATTENTION',
   str(schedule.get('explanation') or 'The Windows 15-minute Local Agent schedule is not healthy.'),False,None,
   'Run UPDATE_LOCAL_AGENT_SCHEDULE.ps1 or review Windows Task Scheduler.'))
 if str(ku.get('status') or '').upper() not in {'OK','HEALTHY'}:
  rows.append(item('KUCOIN_ACCOUNT_DATA','KuCoin account data needs attention','Trading data','high','ATTENTION',
   str(ku.get('message') or ku.get('api_message') or 'KuCoin balance/account refresh is not healthy.'),True,'scripts.kucoin_account_sync','Check the KuCoin API connection if automatic retry fails.'))
 if order_problem:
  diag=str(orders.get('diagnosis') or 'One or more KuCoin order requests did not complete.')
  rows.append(item('KUCOIN_TRADING_DATA','KuCoin order monitoring is recovering','Trading data','high','RECOVERING',
   diag+' Dependent checks: trading safety and freshness confirmation.',True,'scripts.kucoin_order_state',
   'No action is normally required while CRM is recovering. Review KuCoin API access only if repeated symbol-aware retries still fail.'))
 if str(fills.get('status') or '').upper() not in {'OK','HEALTHY'}:
  rows.append(item('KUCOIN_FILL_HISTORY','KuCoin trade history is recovering','Profit & loss','medium','RECOVERING',
   str(fills.get('progress_explanation') or fills.get('api_message') or 'Fill-history retrieval has not completed.'),True,'scripts.kucoin_fill_ledger','No manual action unless repeated retries fail.'))
 elif account.get('realised_profit_quote') is None:
  rows.append(item('REALIZED_PNL_BUILDING','Realised P/L is still reconciling','Profit & loss','low','UPDATING',
   str(fills.get('progress_explanation') or 'Closed fills still need complete cost basis.'),True,'scripts.independent_trade_accounting_engine','CRM will retry automatically; no manual action is normally required.'))
 if fresh.get('overall') in {'ACTION_REQUIRED','SOURCE_OVERDUE'} and not order_problem and schedule.get('status') not in {'MISSING','DISABLED','ERROR'}:
  rows.append(item('FRESHNESS_HEADLINE','Trading data freshness needs attention','Refresh','high','ATTENTION',
   str(fresh.get('overall_reason') or 'A decision-critical refresh condition is blocking the dashboard.'),True,'scripts.freshness_controller','Open details only if automatic recovery cannot restore current data.'))
 if str(assure.get('status') or '').upper() not in {'HEALTHY','OK'} and not order_problem:
  rows.append(item('TRADING_SAFETY','Trading safety checks are incomplete','Trading safety','high','ATTENTION',
   f"{(assure.get('summary') or {}).get('failed',0)} failed and {(assure.get('summary') or {}).get('attention',0)} attention item(s).",True,'scripts.execution_assurance_engine','Review the affected live trade if protection remains unverified.'))
 if present.get('result') not in {None,'HEALTHY'} or (ui.get('overall') or {}).get('state') not in {None,'HEALTHY'}:
  rows.append(item('INTERFACE_QUALITY','Dashboard layout/formatting check needs attention','Interface','medium','ATTENTION',
   'One or more presentation checks found a formatting inconsistency.',False,None,'The release should not publish until shared UI validation passes.'))
 live=str(((sync.get('components') or {}).get('live_pages') or {}).get('status') or '').upper()
 if live in {'FAILED','ERROR','DELAYED','BEHIND'}:
  rows.append(item('PUBLICATION','Website update is delayed','Publication','low','DELAYED',
   'Trading data can remain usable even while the newest dashboard publication is delayed.',False,None,'Normally wait for the publisher; investigate only if the delay persists.'))
 tc=str(three.get('overall_status') or three.get('status') or '').upper()
 if tc in {'ERROR','FAILED','DEGRADED'}:
  rows.append(item('THREECOMMAS','3Commas monitoring is degraded','Provider monitoring','low','ATTENTION',
   'KuCoin remains authoritative; 3Commas is temporary secondary telemetry.',False,None,'Check the 3Commas ↔ KuCoin exchange connection if trading through 3Commas is affected.'))
 return rows

def repair(rows):
 results=[]
 safe_order=[
  ('KUCOIN_ACCOUNT_DATA','scripts.kucoin_account_sync',()),
  ('KUCOIN_TRADING_DATA','scripts.kucoin_order_state',()),
  ('KUCOIN_FILL_HISTORY','scripts.kucoin_fill_ledger',()),
  ('REALIZED_PNL_BUILDING','scripts.independent_trade_accounting_engine',()),
  ('FRESHNESS_HEADLINE','scripts.freshness_controller',()),
  ('TRADING_SAFETY','scripts.execution_assurance_engine',()),
 ]
 codes={x['code'] for x in rows}
 for code,mod,args in safe_order:
  if code not in codes:continue
  rc,out=runmod(mod,*args);results.append({'code':code,'module':mod,'result':'REPAIRED_OR_REFRESHED' if rc==0 else 'FAILED','detail':out})
 # Always rebuild dependent read-only summaries after any repair attempt.
 if results:
  for mod in ['scripts.independent_trade_accounting_engine','scripts.live_portfolio_truth_engine','scripts.freshness_controller','scripts.source_health_engine']:
   rc,out=runmod(mod);results.append({'code':'DEPENDENT_REFRESH','module':mod,'result':'PASS' if rc==0 else 'FAILED','detail':out})
 return results

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repair',action='store_true');a=ap.parse_args()
 before=diagnose();repairs=repair(before) if a.repair else [];after=diagnose()
 blocking=[x for x in after if x['severity']=='high' and x['state']=='ATTENTION']
 recovering=[x for x in after if x['state'] in {'RECOVERING','UPDATING','DELAYED'}]
 updating=[x for x in after if x['state'] in {'UPDATING','DELAYED'}]
 overall='ACTION_REQUIRED' if blocking else ('RECOVERING_AUTOMATICALLY' if recovering else ('UPDATING' if updating or after else 'HEALTHY'))
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'overall':overall,'summary':{'issues_before':len(before),'issues_after':len(after),'automatic_repairs_attempted':len(repairs),'blocking_after':len(blocking)},
  'issues':after,'repair_log':repairs[-30:],
  'safe_repair_policy':['read-only API refresh','local generated-output regeneration','accounting/freshness recomputation'],
  'never_automatic':['place/cancel KuCoin orders','change API credentials','start/stop/edit 3Commas bots','Git push/force push','change capital allocation'],
  'next_action':('Review the remaining blocking item(s).' if blocking else ('No manual action required. CRM is repairing/retrying the affected data path automatically.' if recovering else 'No manual action required; CRM will continue checking itself automatically.'))}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'CRM Health & Recovery: {overall}; before={len(before)} after={len(after)} repairs={len(repairs)}')
 return 0 if not blocking else 1

if __name__=='__main__':raise SystemExit(main())
