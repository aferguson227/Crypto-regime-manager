#!/usr/bin/env python3
"""V44 user-friendly freshness controller.

Turns raw ages into Current / Refresh due / Attention states matched to the
actual collection cadence. It does not call external APIs or mutate trading.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'freshness_status.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
 except Exception:return {}
def dt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return None
def mins(v):
 x=dt(v); return None if not x else round((datetime.now(timezone.utc)-x).total_seconds()/60,1)
def human(m):
 if m is None:return 'Unknown'
 m=max(0,int(round(m)))
 if m<60:return f'{m} min ago'
 h=m//60; mm=m%60
 if h<24:return f'{h}h {mm:02d}m ago'
 d=h//24; hh=h%24; return f'{d}d {hh}h ago'
def state(age,current,due):
 if age is None:return ('ATTENTION','No successful refresh timestamp is available.')
 if age<=current:return ('CURRENT','Within expected refresh cadence.')
 if age<=due:return ('REFRESH_DUE','Refresh is due soon; last validated data remains usable.')
 return ('ATTENTION','Refresh is overdue; review the relevant collector if this persists.')
def row(name,age,expected,current,due,source):
 st,note=state(age,current,due)
 return {'name':name,'status':st,'age_minutes':age,'age_display':human(age),'expected_cadence_minutes':expected,'next_refresh_guidance':note,'source':source}
def main():
 tc=load('threecommas.json'); agent=load('local_agent_status.json'); cloud=load('cloud_reliability.json'); diag=load('diagnostics_runtime.json') or load('diagnostics.json')
 tc_age=mins(tc.get('last_success_at') or tc.get('generated_at'))
 local_age=mins(agent.get('generated_at'))
 app_pipe=(cloud.get('pipelines') or {}).get('application') or {}
 app_age=None
 if app_pipe.get('last_success_age_hours') is not None:
  try: app_age=round(float(app_pipe.get('last_success_age_hours'))*60,1)
  except: pass
 rows=[
  row('3Commas',tc_age,60,90,180,'GitHub CRM Data Refresh'),
  row('Local private data',local_age,15,30,75,'Windows Local Agent'),
  row('Application publication',app_age,60,120,480,'Validated application/cloud publication'),
  row('Diagnostics',mins(diag.get('generated_at')),15,60,360,'Autonomous diagnostics')]
 overall='CURRENT' if all(r['status']=='CURRENT' for r in rows[:2]) else ('ATTENTION' if any(r['status']=='ATTENTION' for r in rows[:2]) else 'REFRESH_DUE')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'overall':overall,'components':rows,
          'wording_policy':'Use Current, Refresh due and Attention. Do not describe expected age alone as stale.','automatic_refresh':{'local_agent_minutes':15,'threecommas_target_minutes':60,'full_diagnostics_manual_required':False},'read_only':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Freshness status written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
