#!/usr/bin/env python3
"""GitHub Actions and Pages engineering intelligence for CRM V38.
Works from published workflow telemetry when available and always validates the
local workflow contract. It never changes secrets or trading configuration.
"""
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'github_actions_health.json'
def load(p,default):
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except Exception:return default
def main():
 now=datetime.now(timezone.utc).isoformat(); policy=load(ROOT/'config/workflow_policy.json',{}); history=load(DOCS/'workflow_history.json',{'runs':[]}); runs=history.get('runs') or []
 issues=[]; workflows={}
 for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
  text=p.read_text(encoding='utf-8',errors='replace'); workflows[p.name]={'deploy_pages':bool(re.search(r'actions/deploy-pages@',text)),'upload_pages':bool(re.search(r'actions/upload-pages-artifact@',text)),'module_execution':not bool(re.search(r'run:\s*python\s+scripts[/\\]',text))}
 pages=[n for n,v in workflows.items() if v['deploy_pages']]
 if len(pages)!=1:issues.append({'fingerprint':'DUPLICATE_PAGES_PUBLISHER','severity':'critical','title':'Pages publisher count is not one','detail':f'Found {len(pages)} publishers: {pages}','safe_action':'Restore the canonical single-publisher workflow.'})
 page_path=ROOT/'.github/workflows/pages-deploy.yml'; text=page_path.read_text(encoding='utf-8') if page_path.exists() else ''
 if 'cancel-in-progress: false' not in text:issues.append({'fingerprint':'PAGES_CONCURRENCY_DRIFT','severity':'critical','title':'Pages concurrency is not queue-safe','detail':'Active deployments may be cancelled by later commits.','safe_action':'Restore cancel-in-progress: false.'})
 m=re.search(r'timeout-minutes:\s*(\d+)',text); timeout=int(m.group(1)) if m else None
 if timeout is None or timeout<30:issues.append({'fingerprint':'PAGES_TIMEOUT_TOO_SHORT','severity':'warning','title':'Pages timeout is below approved threshold','detail':f'Configured timeout: {timeout}.','safe_action':'Restore the approved 30-minute timeout.'})
 active=[]
 for r in runs[-100:]:
  status=str(r.get('status','')).lower(); dur=r.get('duration_seconds')
  if status in {'queued','waiting'}: active.append({'fingerprint':'PAGES_DEPLOYMENT_QUEUED','severity':'warning','run':r})
  elif status in {'cancelled','canceled'}: active.append({'fingerprint':'PAGES_DEPLOYMENT_CANCELLED','severity':'warning','run':r})
  elif status in {'timed_out','timeout'}: active.append({'fingerprint':'PAGES_DEPLOYMENT_TIMEOUT','severity':'critical','run':r})
  if isinstance(dur,(int,float)) and dur>900:active.append({'fingerprint':'WORKFLOW_SLOWDOWN','severity':'warning','run':r})
 issues.extend(active)
 durations=[float(r['duration_seconds']) for r in runs if isinstance(r.get('duration_seconds'),(int,float)) and str(r.get('status')).lower()=='success']
 median=sorted(durations)[len(durations)//2] if durations else None
 state='CRITICAL' if any(x.get('severity')=='critical' for x in issues) else ('WARNING' if issues else 'HEALTHY')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'state':state,'workflow_count':len(workflows),'single_pages_publisher':len(pages)==1,'pages_publishers':pages,'pages_timeout_minutes':timeout,'queue_safe': 'cancel-in-progress: false' in text,'successful_duration_median_seconds':median,'telemetry_runs':len(runs),'issues':issues,'workflows':workflows,'repair_policy':{'max_automatic_retries':2,'backoff_minutes':[5,15],'never_force_push':True,'never_change_secrets':True,'never_change_trading':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'GitHub Actions health written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
