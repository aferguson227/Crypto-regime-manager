#!/usr/bin/env python3
"""Run staged CRM engineering audits without doing unnecessary work."""
from __future__ import annotations
import argparse,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/engineering_schedule.json'
MODES={'quick':['scripts.github_actions_intelligence_engine','scripts.self_healing_engine'], 'hourly':['scripts.operational_intelligence_engine','scripts.github_actions_intelligence_engine','scripts.self_healing_engine','scripts.issue_lifecycle_engine'], 'daily':['scripts.repository_hygiene_engine','scripts.ui_health_engine','scripts.github_actions_intelligence_engine','scripts.decision_quality_engine','scripts.self_healing_engine','scripts.issue_lifecycle_engine','scripts.engineering_intelligence_engine'], 'pre-release':['scripts.workflow_policy','scripts.repository_hygiene_engine','scripts.operational_intelligence_engine','scripts.github_actions_intelligence_engine','scripts.decision_quality_engine','scripts.ui_health_engine','scripts.ui_consistency','scripts.self_healing_engine','scripts.issue_lifecycle_engine','scripts.engineering_intelligence_engine']}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=MODES,default='quick');a=ap.parse_args();started=time.time();steps=[]
 for m in MODES[a.mode]:
  t=time.time();r=subprocess.run(['python','-m',m],cwd=ROOT);steps.append({'module':m,'result':'pass' if r.returncode==0 else 'fail','seconds':round(time.time()-t,2)})
  if r.returncode:return r.returncode
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':a.mode,'duration_seconds':round(time.time()-started,2),'steps':steps,'result':'pass'};OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Engineering {a.mode} audit complete in {payload["duration_seconds"]}s');return 0
if __name__=='__main__':raise SystemExit(main())
