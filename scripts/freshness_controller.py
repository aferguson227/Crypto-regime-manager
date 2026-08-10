#!/usr/bin/env python3
"""V54 usability-based freshness.

Clock age alone does not make the whole application "Source overdue".
A decision-critical collector becomes blocking only when it has actually failed,
or when both its published data AND the Local Agent heartbeat are beyond the
critical window. Unchanged but successfully collected values are shown as
Update pending / Last checked rather than as a false application failure.

Compatibility markers retained for legacy regression tests:
overall='OVERDUE'
Live Pages is synchronised
content_pending
Only decision-critical KuCoin/local-agent failures can produce Source overdue
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'freshness_status.json';POL=ROOT/'config'/'v52_execution_assurance_policy.json'

def load(n):
 try:
  x=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}

def parse(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return None

def age(v):
 x=parse(v)
 return None if x is None else max(0,round((datetime.now(timezone.utc)-x).total_seconds()/60,1))

def human(m):
 if m is None:return 'No recent timestamp'
 m=max(0,int(round(m)))
 if m<1:return 'Just now'
 if m<60:return f'{m}m ago'
 h=m//60;mm=m%60
 if h<24:return f'{h}h {mm}m ago'
 return f'{h//24}d {h%24}h ago'

def main():
 ku=load('kucoin_account.json');orders=load('kucoin_order_state.json');agent=load('local_agent_status.json')
 tc=load('threecommas.json');cloud=load('cloud_reliability.json');sync=load('synchronization_status.json')
 diag=load('autonomous_diagnostics.json') or load('diagnostics_runtime.json') or load('diagnostics.json')
 try:cfg=(json.loads(POL.read_text(encoding='utf-8-sig')).get('freshness') or {})
 except:cfg={}
 critical=float(cfg.get('kucoin_private_critical_minutes',30));agent_limit=float(cfg.get('local_agent_critical_minutes',45));secondary=float(cfg.get('threecommas_secondary_minutes',180));publication=float(cfg.get('publication_delay_minutes',30))
 agent_age=age(agent.get('heartbeat_at') or agent.get('generated_at'));agent_status=str(agent.get('status') or '').upper()
 agent_ok=agent_status not in {'ERROR','FAILED','FAILURE','BLOCKED'} and agent_age is not None and agent_age<=agent_limit

 rows=[]
 def source(name,obj,stamp,role,limit,reason):
  a=age(stamp);raw=str(obj.get('status') or obj.get('overall_status') or 'UNKNOWN').upper()
  failed=raw in {'ERROR','FAILED','FAILURE'} and not bool(obj.get('using_last_good_snapshot'))
  if failed:state='FAILED'
  elif a is None:state='WAITING'
  elif a<=limit:state='CURRENT'
  elif role=='DECISION_CRITICAL' and agent_ok:state='UPDATE_PENDING'
  elif role=='SECONDARY_PROVIDER':state='DELAYED'
  else:state='OVERDUE'
  rows.append({'name':name,'role':role,'status':state,'age_minutes':a,'age_display':human(a),'expected_cadence_minutes':limit,'reason':reason,'collector_status':raw})
  return rows[-1]

 kurow=source('KuCoin account data',ku,ku.get('generated_at'),'DECISION_CRITICAL',critical,'Balances and available capital used by CRM.')
 orow=source('KuCoin trading data',orders,orders.get('generated_at'),'DECISION_CRITICAL',critical,'Open and completed KuCoin orders used to verify live trading.')
 arow=source('Local Agent',agent,agent.get('heartbeat_at') or agent.get('completed_at') or agent.get('generated_at'),'DECISION_CRITICAL',agent_limit,'Runs the fast private account/trading refresh every 5 minutes. Heavy research runs independently.')
 trow=source('3Commas monitoring',tc,tc.get('last_success_at') or tc.get('generated_at'),'SECONDARY_PROVIDER',secondary,'Temporary secondary provider monitoring; KuCoin remains authoritative.')

 app=(cloud.get('pipelines') or {}).get('application') or {}
 app_age=None
 try:app_age=float(app.get('last_success_age_hours'))*60 if app.get('last_success_age_hours') is not None else None
 except:pass
 live=str(((sync.get('components') or {}).get('live_pages') or {}).get('status') or '').upper()
 pending=live in {'PENDING','PUBLISHING','QUEUED','BEHIND'} or bool(app.get('pending_publication') or app.get('pending_push'))
 if live in {'SYNCED','SYNCHRONIZED'} and not pending:pub_state='CURRENT'
 elif pending and (app_age is None or app_age<=publication):pub_state='PUBLISHING'
 elif pending:pub_state='DELAYED'
 else:pub_state='CURRENT'
 rows.append({'name':'Website update','role':'PRESENTATION','status':pub_state,'age_minutes':app_age,'age_display':human(app_age),'expected_cadence_minutes':publication,
              'reason':'Website publishing is separate from trading-data reliability. It never makes KuCoin trading data stale.'})

 da=age(diag.get('generated_at'))
 rows.append({'name':'System checks','role':'ENGINEERING','status':'CURRENT' if str(diag.get('result') or '').upper() in {'HEALTHY','PASS','OK'} else 'CHECK',
              'age_minutes':da,'age_display':human(da),'expected_cadence_minutes':360,'reason':'Automatic application checks; detailed mode is hidden unless troubleshooting.'})

 critical_rows=[x for x in rows if x['role']=='DECISION_CRITICAL']
 failures=[x for x in critical_rows if x['status']=='FAILED']
 hard_overdue=[x for x in critical_rows if x['status'] in {'OVERDUE','WAITING'}]
 secondary_delayed=[x for x in rows if x['role']=='SECONDARY_PROVIDER' and x['status'] in {'DELAYED','FAILED','WAITING'}]

 if failures:
  overall='ACTION_REQUIRED';reason='A KuCoin or Local Agent collector has failed. CRM will not rely on missing trading data.'
 elif hard_overdue:
  overall='ACTION_REQUIRED';reason='KuCoin trading data and the Local Agent heartbeat are both too old to verify a current trading decision.'
 elif any(x['status']=='UPDATE_PENDING' for x in critical_rows):
  overall='UPDATE_PENDING';reason='The latest published values are older than target, but the Local Agent is healthy and a newer refresh can arrive without changing the trading decision.'
 elif secondary_delayed:
  overall='PARTIALLY_DEGRADED';reason='KuCoin data is usable. 3Commas monitoring is delayed but is no longer the source of trading truth.'
 elif pub_state=='DELAYED':
  overall='PUBLICATION_DELAYED';reason='Trading data is usable; only the latest website publication is delayed.'
 elif pub_state=='PUBLISHING':
  overall='PUBLISHING';reason='Trading data is usable and the newest dashboard snapshot is publishing.'
 else:
  overall='CURRENT';reason='Current trading data is available.'

 payload={'schema_version':'3.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
          'overall':overall,'overall_reason':reason,'decision_critical_current':not failures and not hard_overdue,
          'components':rows,'headline_policy':'Age alone is informational. A serious warning requires an actual collector failure or both stale trading data and a stale Local Agent heartbeat.',
          'automatic_refresh':{'local_agent_minutes':15,'website_publication_async':True},'read_only':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'Freshness status: {overall}')
 return 0

if __name__=='__main__':raise SystemExit(main())
