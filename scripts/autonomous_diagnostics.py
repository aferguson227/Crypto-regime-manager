#!/usr/bin/env python3
"""V44 autonomous diagnostics controller.
Quick checks run every Local Agent cycle; deeper health checks at most hourly.
Full release tests remain a build/release concern, not a routine user task.
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'autonomous_diagnostics.json'
def load():
 try:return json.loads(OUT.read_text(encoding='utf-8-sig'))
 except:return {}
def age_minutes(v):
 try:
  x=datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc); return (datetime.now(timezone.utc)-x).total_seconds()/60
 except:return 1e9
def runmod(m,*args):
 r=subprocess.run([sys.executable,'-m',m,*args],cwd=ROOT); return r.returncode
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--full',action='store_true'); a=ap.parse_args(); prev=load(); now=datetime.now(timezone.utc).isoformat(); steps=[]
 # Always-run lightweight checks.
 for mod,args in [('scripts.repository_guardian',('scan',)),('scripts.freshness_controller',()),('scripts.self_healing_engine',())]:
  rc=runmod(mod,*args); steps.append({'module':mod,'result':'pass' if rc==0 else 'fail'}); 
  if rc:return rc
 deeper=a.full or age_minutes(prev.get('last_hourly_at'))>=60
 if deeper:
  for mod,args in [('scripts.engineering_scheduler',('--mode','hourly')),('scripts.ui_validation_manager',())]:
   rc=runmod(mod,*args); steps.append({'module':mod,'result':'pass' if rc==0 else 'fail'})
   if rc:return rc
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'mode':'hourly' if deeper else 'quick','result':'HEALTHY','steps':steps,
          'last_hourly_at':now if deeper else prev.get('last_hourly_at'),'full_release_validation_required':False,'automatic':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Autonomous diagnostics: HEALTHY ({payload["mode"]})'); return 0
if __name__=='__main__':raise SystemExit(main())
