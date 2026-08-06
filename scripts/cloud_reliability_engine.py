#!/usr/bin/env python3
"""V32.7 cloud automation watchdog and workflow self-checks."""
from __future__ import annotations
import json, os, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUTPUT=DOCS/'cloud_reliability.json'

def load(path:Path)->dict[str,Any]:
 try:
  x=json.loads(path.read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except Exception:return {}
def dt(value:Any):
 try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).astimezone(timezone.utc)
 except Exception:return None
def age_hours(value:Any)->float|None:
 d=dt(value);return round((datetime.now(timezone.utc)-d).total_seconds()/3600,2) if d else None
def freshness(name:str,stamp:Any,expected:float,warning:float,failure:float,status:str|None=None)->dict[str,Any]:
 age=age_hours(stamp)
 state='unknown' if age is None else 'failure' if age>failure else 'warning' if age>warning else 'healthy'
 if status in {'error','fail'}:state='failure'
 return {'name':name,'observed_at':stamp,'age_hours':age,'expected_cadence_hours':expected,'warning_after_hours':warning,'failure_after_hours':failure,'state':state,'source_status':status}
def workflow_check(path:Path,expected_module:str,cron_hint:str)->dict[str,Any]:
 text=path.read_text(encoding='utf-8') if path.exists() else ''
 findings=[]
 if 'workflow_dispatch:' not in text:findings.append('Manual recovery trigger is missing.')
 if 'schedule:' not in text or 'cron:' not in text:findings.append('Scheduled trigger is missing.')
 if expected_module not in text:findings.append(f'Module execution is missing: {expected_module}')
 if 'permissions:' not in text or 'contents: write' not in text:findings.append('Explicit contents write permission is missing.')
 if cron_hint not in text:findings.append(f'Expected cron not found: {cron_hint}')
 direct=re.findall(r'run:\s*python\s+(scripts/[^\s]+\.py)',text)
 if direct:findings.append('Direct script execution may break package imports: '+', '.join(direct))
 return {'file':str(path.relative_to(ROOT)),'status':'pass' if not findings else 'fail','findings':findings,'module_execution':expected_module,'expected_cron':cron_hint}
def build()->dict[str,Any]:
 three=load(DOCS/'threecommas.json');cloud=load(DOCS/'cloud_status.json')
 endpoints=three.get('endpoint_diagnostics') if isinstance(three.get('endpoint_diagnostics'),dict) else {}
 sources=[freshness('3Commas read-only sync',three.get('generated_at'),1,1.5,3,three.get('status')),freshness('Main market/application refresh',cloud.get('completed_at'),4,5,9,cloud.get('state'))]
 workflows=[workflow_check(ROOT/'.github/workflows/threecommas-update.yml','python -m scripts.threecommas_sync','37 * * * *'),workflow_check(ROOT/'.github/workflows/multi-coin-update.yml','python -m scripts.cloud_update','18 0,4,8,12,16,20 * * *')]
 failures=[x for x in sources if x['state']=='failure']+[x for x in workflows if x['status']=='fail']
 warnings=[x for x in sources if x['state']=='warning']
 status='FAILURE' if failures else 'WARNING' if warnings else 'HEALTHY'
 repo=os.getenv('GITHUB_REPOSITORY');run=os.getenv('GITHUB_RUN_ID')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'snapshot_id':hashlib.sha256(json.dumps({'three':three.get('generated_at'),'cloud':cloud.get('completed_at')},sort_keys=True).encode()).hexdigest()[:20],'status':status,'sources':sources,'threecommas_endpoints':endpoints,'workflows':workflows,'github':{'repository':repo,'workflow_run_id':run,'run_url':f'https://github.com/{repo}/actions/runs/{run}' if repo and run else None},'automation_policy':{'routine_manual_runs_required':False,'manual_run_purpose':'Recovery and diagnosis only','threecommas_cadence':'hourly at minute 37 UTC','main_refresh_cadence':'every four hours at minute 18 UTC'},'read_only':True}
 return payload
def main():
 p=build();OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Cloud reliability written: {OUTPUT}');return 0
if __name__=='__main__':raise SystemExit(main())
