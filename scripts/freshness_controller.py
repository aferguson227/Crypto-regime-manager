#!/usr/bin/env python3
"""V45 freshness status: age is not a fault.
Only a collector error or materially overdue required source becomes Action required.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'freshness_status.json'
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
 if m<60:return f'{m} min ago'
 h=m//60;mm=m%60
 if h<24:return f'{h}h {mm:02d}m ago'
 return f'{h//24}d {h%24}h ago'
def classify(age,current,due,error=False):
 if error:return 'ACTION_REQUIRED','Collector reported an error; review diagnostics.'
 if age is None:return 'AWAITING_FIRST_REFRESH','No validated timestamp yet; the next automatic collector run will populate it.'
 if age<=current:return 'CURRENT','Within the expected automatic refresh window.'
 if age<=due:return 'REFRESH_DUE','Valid data remains available; the next automatic refresh is due.'
 return 'OVERDUE','Automatic refresh is overdue. If this persists, inspect the collector.'
def row(name,age,expected,current,due,source,error=False,automatic=True):
 st,reason=classify(age,current,due,error);return {'name':name,'status':st,'age_minutes':age,'age_display':human(age),'expected_cadence_minutes':expected,'reason':reason,'source':source,'automatic':automatic}
def main():
 tc=load('threecommas.json');agent=load('local_agent_status.json');ku=load('kucoin_account.json');cloud=load('cloud_reliability.json');sync=load('synchronization_status.json');diag=load('autonomous_diagnostics.json') or load('diagnostics_runtime.json') or load('diagnostics.json')
 tc_age=mins(tc.get('last_success_at') or tc.get('generated_at'));local_age=mins(agent.get('generated_at') or ku.get('generated_at'))
 app=(cloud.get('pipelines') or {}).get('application') or {};app_age=None
 try:app_age=round(float(app.get('last_success_age_hours'))*60,1) if app.get('last_success_age_hours') is not None else None
 except:pass
 rows=[row('3Commas',tc_age,60,90,180,'GitHub CRM Data Refresh',str(tc.get('overall_status') or tc.get('status') or '').lower() in {'error','failed'}),row('Local private data',local_age,15,30,75,'Windows Local Agent / KuCoin',str(agent.get('status') or '').upper()=='ERROR')]
 approw=row('Website publication',app_age,240,360,720,'Validated Pages publication')
 syncpages=((sync.get('components') or {}).get('live_pages') or {}).get('status')
 pending=bool(app.get('pending_publication') or app.get('pending_push')) or str(syncpages or '').upper() in {'PENDING','BEHIND','OUT_OF_SYNC'}
 if str(syncpages or '').upper()=='SYNCED' and not pending:
  approw['status']='CURRENT';approw['reason']='Live Pages is synchronised with the published CRM version. Deployment age is informational only.'
 elif not pending and approw['status'] in {'REFRESH_DUE','OVERDUE'}:
  approw['status']='CURRENT';approw['reason']='No newer application content is known to be awaiting publication.'
 approw['content_pending']=pending;approw['synchronization_status']=syncpages
 rows += [approw,row('Diagnostics',mins(diag.get('generated_at')),15,60,360,'Autonomous diagnostics')]
 # Age alone is never generic ATTENTION. Action required is reserved for real collector errors.
 if any(x['status']=='ACTION_REQUIRED' for x in rows):overall='ACTION_REQUIRED'
 elif any(x['status']=='OVERDUE' for x in rows[:2]):overall='OVERDUE'
 elif any(x['status'] in {'REFRESH_DUE','AWAITING_FIRST_REFRESH'} for x in rows[:2]):overall='REFRESH_DUE'
 else:overall='CURRENT'
 payload={'schema_version':'1.1','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'overall':overall,'overall_reason':next((x['reason'] for x in rows if x['status']==overall), 'All required collectors are current.'),'components':rows,'automatic_refresh':{'local_agent_minutes':15,'threecommas_target_minutes':60,'diagnostics_quick_each_agent_cycle':True,'diagnostics_deep_minutes':60,'manual_routine_diagnostics_required':False},'read_only':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Freshness status written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
