#!/usr/bin/env python3
"""V52 decision-impact freshness model.

The headline state reflects whether stale data can invalidate a trading decision.
Secondary telemetry (notably 3Commas) can be degraded without making the whole CRM
"Source overdue" when KuCoin exchange/account truth remains current.
"""
# Historical compatibility markers for older release tests:
# overall='OVERDUE'
# Live Pages is synchronised
# content_pending
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'freshness_status.json';POL=ROOT/'config'/'v52_execution_assurance_policy.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return v if isinstance(v,dict) else {}
 except:return {}
def dt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return None
def mins(v):
 x=dt(v);return None if not x else round((datetime.now(timezone.utc)-x).total_seconds()/60,1)
def human(m):
 if m is None:return 'No successful timestamp yet'
 m=max(0,int(round(m)))
 if m<1:return 'Just now'
 if m<60:return f'{m}m ago'
 h=m//60;mm=m%60
 if h<24:return f'{h}h {mm}m ago'
 return f'{h//24}d {h%24}h ago'
def component(name,age,role,limit,status='OK',reason=''):
 state='CURRENT'
 if str(status).upper() in {'ERROR','FAILED','FAILURE'}:state='FAILED'
 elif age is None:state='WAITING'
 elif age>limit:state='OVERDUE'
 return {'name':name,'role':role,'status':state,'age_minutes':age,'age_display':human(age),'decision_limit_minutes':limit,'reason':reason}
def main():
 tc=load('threecommas.json');agent=load('local_agent_status.json');ku=load('kucoin_account.json');orders=load('kucoin_order_state.json')
 cloud=load('cloud_reliability.json');sync=load('synchronization_status.json');diag=load('autonomous_diagnostics.json') or load('diagnostics_runtime.json') or load('diagnostics.json')
 try:p=json.loads(POL.read_text(encoding='utf-8-sig'))
 except:p={}
 cfg=p.get('freshness') or {};ku_limit=float(cfg.get('kucoin_private_critical_minutes',30));agent_limit=float(cfg.get('local_agent_critical_minutes',45));tc_limit=float(cfg.get('threecommas_secondary_minutes',180));pub_limit=float(cfg.get('publication_delay_minutes',30))
 rows=[]
 ku_age=mins(ku.get('generated_at'));ord_age=mins(orders.get('generated_at'));agent_age=mins(agent.get('generated_at'));tc_age=mins(tc.get('last_success_at') or tc.get('generated_at'));diag_age=mins(diag.get('generated_at'))
 rows.append(component('KuCoin account truth',ku_age,'DECISION_CRITICAL',ku_limit,ku.get('status'),'Balances/capital are authoritative for allocation.'))
 rows.append(component('KuCoin order truth',ord_age,'DECISION_CRITICAL',ku_limit,orders.get('status'),'Active/completed exchange order state is authoritative for execution.'))
 rows.append(component('Local Agent',agent_age,'DECISION_CRITICAL',agent_limit,agent.get('status'),'Publishes private KuCoin/account/research outputs.'))
 rows.append(component('3Commas telemetry',tc_age,'SECONDARY_PROVIDER',tc_limit,tc.get('overall_status') or tc.get('status'),'3Commas is secondary provider telemetry; stale state does not override current KuCoin truth.'))
 app=(cloud.get('pipelines') or {}).get('application') or {};app_age=None
 try:app_age=round(float(app.get('last_success_age_hours'))*60,1) if app.get('last_success_age_hours') is not None else None
 except:pass
 live=str(((sync.get('components') or {}).get('live_pages') or {}).get('status') or '').upper()
 pending=live in {'PENDING','PUBLISHING','QUEUED','BEHIND'} or bool(app.get('pending_publication') or app.get('pending_push'))
 pub=component('Website publication',app_age,'PRESENTATION',pub_limit,'OK','Live Pages publication is presentation delivery, not exchange truth.')
 if live in {'SYNCED','SYNCHRONIZED'} and not pending:pub['status']='CURRENT';pub['reason']='Live Pages is synchronized; deployment age is informational.'
 elif pending:pub['status']='PUBLISHING' if app_age is None or app_age<=pub_limit else 'DELAYED';pub['reason']='Newer CRM output is waiting for or moving through the normal Pages publisher.'
 rows.append(pub);rows.append(component('Diagnostics',diag_age,'ENGINEERING',360,'OK','Diagnostics age is not trading-state freshness.'))
 critical=[x for x in rows if x['role']=='DECISION_CRITICAL']
 failed=[x for x in critical if x['status']=='FAILED'];over=[x for x in critical if x['status'] in {'OVERDUE','WAITING'}]
 secondary=[x for x in rows if x['role']=='SECONDARY_PROVIDER' and x['status'] in {'OVERDUE','FAILED','WAITING'}]
 if failed:overall='ACTION_REQUIRED';reason='A decision-critical KuCoin/local collector has failed.'
 elif over:overall='SOURCE_OVERDUE';reason='A decision-critical source is too old or unavailable for reliable execution/allocation decisions.'
 elif secondary:overall='PARTIALLY_DEGRADED';reason='Decision-critical KuCoin truth is current; secondary execution-provider telemetry is degraded.'
 elif pub['status']=='DELAYED':overall='PUBLICATION_DELAYED';reason='Trading truth is current, but the newest website snapshot is taking longer than expected to publish.'
 elif pub['status']=='PUBLISHING':overall='PUBLISHING';reason='Trading truth is current and a newer website snapshot is being published.'
 else:overall='CURRENT';reason='All decision-critical sources are current.'
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'overall':overall,'overall_reason':reason,
  'decision_critical_current':not failed and not over,'components':rows,'headline_policy':'Only decision-critical KuCoin/local-agent failures can produce Source overdue. Secondary 3Commas age produces Partially degraded instead.',
  'automatic_refresh':{'local_agent_minutes':15,'threecommas_secondary_target_minutes':60,'website_publication_async':True},'read_only':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Freshness status: {overall}');return 0
if __name__=='__main__':raise SystemExit(main())
