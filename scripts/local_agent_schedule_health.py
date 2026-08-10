#!/usr/bin/env python3
"""V66 Windows background-task health: Local Agent + Live Data Service + Research Worker."""
from __future__ import annotations
import json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'local_agent_schedule_health.json'
TASKS=[
 ('CryptoRegimeManager-LocalAgent','5-minute publication/decision refresh'),
 ('CryptoRegimeManager-LiveDataService','resident read-only KuCoin live trading data service'),
 ('CryptoRegimeManager-ResearchWorker','isolated heavy research/backtesting'),
]
def query(name):
 rec={'task_name':name,'exists':None,'enabled':None,'last_run':None,'next_run':None,'last_result':None,'status':'NOT_APPLICABLE'}
 if os.name!='nt':return rec
 r=subprocess.run(['schtasks.exe','/Query','/TN',name,'/V','/FO','LIST'],text=True,capture_output=True)
 rec['exists']=r.returncode==0
 if r.returncode:rec.update(status='MISSING');return rec
 vals={}
 for line in r.stdout.splitlines():
  if ':' in line:
   k,v=line.split(':',1);vals[k.strip().lower()]=v.strip()
 rec['last_run']=vals.get('last run time');rec['next_run']=vals.get('next run time');rec['last_result']=vals.get('last result')
 state=vals.get('scheduled task state') or vals.get('status') or '';rec['enabled']='disabled' not in state.lower()
 rec['status']='HEALTHY' if rec['enabled'] else 'DISABLED';return rec
def main():
 rows=[]
 for name,role in TASKS:
  x=query(name);x['role']=role;rows.append(x)
 local,live,research=rows
 status='HEALTHY' if local['status']=='HEALTHY' and live['status']=='HEALTHY' else ('MISSING' if 'MISSING' in {local['status'],live['status']} else 'ATTENTION')
 payload={'schema_version':'3.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'status':status,'task_name':local['task_name'],'exists':local['exists'],'enabled':local['enabled'],'last_run':local['last_run'],'next_run':local['next_run'],'last_result':local['last_result'],
  'tasks':rows,'live_data_service_status':live['status'],'research_worker_status':research['status'],
  'explanation':('The 5-minute Local Agent and resident KuCoin Live Data Service are enabled; heavy research runs independently.'
                 if status=='HEALTHY' else 'The Local Agent or resident KuCoin Live Data Service schedule needs attention.')}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'Background task health: local={local["status"]} live={live["status"]} research={research["status"]}');return 0
if __name__=='__main__':raise SystemExit(main())
