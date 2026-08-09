#!/usr/bin/env python3
"""V56 Windows Local Agent scheduled-task health."""
from __future__ import annotations
import json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'local_agent_schedule_health.json';TASK='CryptoRegimeManager-LocalAgent'
def main():
 rec={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
 'task_name':TASK,'platform':os.name,'status':'NOT_APPLICABLE','exists':None,'enabled':None,'last_run':None,'next_run':None,'last_result':None,
 'explanation':'Windows Task Scheduler health is checked on the installed Windows CRM host.'}
 if os.name=='nt':
  r=subprocess.run(['schtasks.exe','/Query','/TN',TASK,'/V','/FO','LIST'],text=True,capture_output=True);rec['exists']=r.returncode==0
  if r.returncode:rec.update(status='MISSING',explanation='The 15-minute CRM Local Agent scheduled task was not found.')
  else:
   vals={}
   for line in r.stdout.splitlines():
    if ':' in line:
     k,v=line.split(':',1);vals[k.strip().lower()]=v.strip()
   rec['last_run']=vals.get('last run time');rec['next_run']=vals.get('next run time');rec['last_result']=vals.get('last result')
   state=vals.get('scheduled task state') or vals.get('status') or '';rec['enabled']='disabled' not in state.lower()
   rec['status']='HEALTHY' if rec['enabled'] else 'DISABLED'
   rec['explanation']='The 15-minute Local Agent task exists and is enabled.' if rec['enabled'] else 'The Local Agent scheduled task exists but is disabled.'
 OUT.write_text(json.dumps(rec,indent=2),encoding='utf-8');print(f"Local Agent schedule health: {rec['status']}");return 0
if __name__=='__main__':raise SystemExit(main())
