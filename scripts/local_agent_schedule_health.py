#!/usr/bin/env python3
from __future__ import annotations
import json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.runtime_state_manager import state_dir
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'local_agent_schedule_health.json';LIVE_NAME='CryptoRegimeManager-LiveDataService'
def query_task(name):
 rec={'task_name':name,'mechanism':'scheduled_task','exists':None,'enabled':None,'last_run':None,'next_run':None,'last_result':None,'status':'NOT_APPLICABLE'}
 if os.name!='nt':return rec
 r=subprocess.run(['schtasks.exe','/Query','/TN',name,'/V','/FO','LIST'],text=True,capture_output=True);rec['exists']=r.returncode==0
 if r.returncode:rec['status']='MISSING';return rec
 vals={}
 for line in r.stdout.splitlines():
  if ':' in line:
   k,v=line.split(':',1);vals[k.strip().lower()]=v.strip()
 rec['last_run']=vals.get('last run time');rec['next_run']=vals.get('next run time');rec['last_result']=vals.get('last result')
 state=vals.get('scheduled task state') or vals.get('status') or '';rec['enabled']='disabled' not in state.lower();rec['status']='HEALTHY' if rec['enabled'] else 'DISABLED';return rec
def query_live_startup():
 rec={'task_name':LIVE_NAME,'mechanism':'HKCU startup','exists':None,'enabled':None,'last_run':None,'next_run':'At user logon','last_result':None,'status':'NOT_APPLICABLE'}
 if os.name!='nt':return rec
 r=subprocess.run(['reg.exe','query',r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run','/v',LIVE_NAME],text=True,capture_output=True)
 rec['exists']=r.returncode==0;rec['enabled']=rec['exists'];rec['status']='HEALTHY' if rec['exists'] else 'MISSING';return rec
def load_live_status():
 candidates=[state_dir()/'kucoin_live_service_status.json',DOCS/'kucoin_live_service_status.json']
 best={};best_age=None
 for p in candidates:
  try:d=json.loads(p.read_text(encoding='utf-8-sig'))
  except:continue
  a=age_minutes(d.get('heartbeat_at') or d.get('generated_at'))
  if best_age is None or (a is not None and a<best_age):best=d;best_age=a
 return best
def age_minutes(stamp):
 try:return max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(str(stamp).replace('Z','+00:00'))).total_seconds()/60)
 except:return None
def main():
 local=query_task('CryptoRegimeManager-LocalAgent');live=query_live_startup();research=query_task('CryptoRegimeManager-ResearchWorker')
 runtime=load_live_status();age=age_minutes(runtime.get('heartbeat_at') or runtime.get('generated_at'))
 live['heartbeat_at']=runtime.get('heartbeat_at') or runtime.get('generated_at');live['heartbeat_age_minutes']=round(age,2) if age is not None else None
 live['runtime_status']=runtime.get('status')
 if live['exists'] and age is not None and age<=3 and str(runtime.get('status') or '').upper() in {'HEALTHY','DEGRADED','REFRESHING','STARTING'}:
  live['status']='HEALTHY'
 elif live['exists']:
  live['status']='RECOVERING'
 for x,role in [(local,'5-minute publication/decision refresh'),(live,'resident read-only KuCoin live trading data service'),(research,'isolated heavy research/backtesting')]:x['role']=role
 rows=[local,live,research]
 status='HEALTHY' if local['status']=='HEALTHY' and live['status']=='HEALTHY' else ('MISSING' if 'MISSING' in {local['status'],live['status']} else 'ATTENTION')
 payload={'schema_version':'4.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'status':status,'task_name':local['task_name'],'exists':local['exists'],'enabled':local['enabled'],'last_run':local['last_run'],'next_run':local['next_run'],'last_result':local['last_result'],
  'tasks':rows,'live_data_service_status':live['status'],'live_data_service_mechanism':'HKCU per-user startup','live_data_service_heartbeat_age_minutes':live.get('heartbeat_age_minutes'),
  'research_worker_status':research['status'],
  'explanation':('Local Agent and resident KuCoin service are both current; heavy research remains isolated.'
                 if status=='HEALTHY' else ('The resident KuCoin service is registered and CRM is attempting automatic recovery.' if live['exists'] else 'The per-user KuCoin Live Data Service startup registration is missing.'))}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'Background service health: local={local["status"]} live={live["status"]} age={live.get("heartbeat_age_minutes")} research={research["status"]}');return 0
if __name__=='__main__':raise SystemExit(main())
