#!/usr/bin/env python3
"""GitHub Actions engineering intelligence for CRM V39.1."""
from __future__ import annotations
import json,re,statistics
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'github_actions_health.json'
def load(p,default):
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except Exception:return default

def deploy_timeout(text:str):
 m=re.search(r'(?ms)^  deploy:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)',text)
 if not m:return None
 x=re.search(r'^    timeout-minutes:\s*(\d+)\s*$',m.group(1),re.M)
 return int(x.group(1)) if x else None

def main():
 now=datetime.now(timezone.utc); policy=load(ROOT/'config/workflow_policy.json',{}); history=load(DOCS/'workflow_history.json',{'runs':[]}); runs=history.get('runs') or []
 issues=[]; workflows={}
 for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
  text=p.read_text(encoding='utf-8',errors='replace'); gm=re.search(r'group:\s*([^\s]+)',text)
  workflows[p.name]={'deploy_pages':bool(re.search(r'actions/deploy-pages@',text)),'upload_pages':bool(re.search(r'actions/upload-pages-artifact@',text)),'module_execution':not bool(re.search(r'run:\s*python\s+scripts[/\\]',text)),'concurrency_group':gm.group(1) if gm else None}
 pages=[n for n,v in workflows.items() if v['deploy_pages']]
 if len(pages)!=1:issues.append({'fingerprint':'DUPLICATE_PAGES_PUBLISHER','severity':'critical','title':'Pages publisher count is not one','detail':f'Found {len(pages)} publishers: {pages}','safe_action':'Restore the canonical single-publisher workflow.'})
 page_path=ROOT/'.github/workflows/pages-deploy.yml'; text=page_path.read_text(encoding='utf-8') if page_path.exists() else ''
 if 'cancel-in-progress: false' not in text:issues.append({'fingerprint':'PAGES_CONCURRENCY_DRIFT','severity':'critical','title':'Pages concurrency is not queue-safe','detail':'Active deployments may be cancelled by later commits.','safe_action':'Restore cancel-in-progress: false.'})
 timeout=deploy_timeout(text)
 if timeout is None or timeout<30:issues.append({'fingerprint':'PAGES_TIMEOUT_TOO_SHORT','severity':'warning','title':'Pages deploy timeout is below approved threshold','detail':f'Deploy timeout: {timeout}.','safe_action':'Restore the approved 30-minute deploy timeout.'})
 # Duplicate concurrency groups are a real configuration issue.
 groups={}
 for name,row in workflows.items():
  g=row.get('concurrency_group')
  if g and g in groups:issues.append({'fingerprint':'WORKFLOW_CONCURRENCY_COLLISION','severity':'critical','title':'Workflows share a concurrency group','detail':f'{name} and {groups[g]} share {g}.','safe_action':'Restore isolated canonical concurrency groups.'})
  elif g:groups[g]=name
 # Only current canonical workflows can create active incidents. Retired workflow names remain historical evidence.
 canonical_names=set()
 for wf in (ROOT/'.github/workflows').glob('*.yml'):
  txt=wf.read_text(encoding='utf-8',errors='replace')
  m=re.search(r'^name:\s*(.+?)\s*$',txt,re.M)
  if m: canonical_names.add(m.group(1).strip().strip('"\''))
 latest={}
 for r in runs:
  name=r.get('name') or 'Workflow'
  if name not in canonical_names: continue
  if name not in latest: latest[name]=r
 historical={'cancelled':0,'failed':0,'timed_out':0,'successful':0}
 for r in runs[-100:]:
  st=str(r.get('status','')).lower()
  if st=='success': historical['successful']+=1
  elif st in {'cancelled','canceled'}: historical['cancelled']+=1
  elif st in {'timed_out','timeout'}: historical['timed_out']+=1
  elif st in {'failure','failed'}: historical['failed']+=1
 for name,r in latest.items():
  status=str(r.get('status','')).lower(); queue=r.get('queue_seconds'); dur=r.get('duration_seconds')
  if status=='queued' and isinstance(queue,(int,float)) and queue>=300:
   sev='warning' if queue<600 else 'critical'
   issues.append({'fingerprint':'GITHUB_HOSTED_RUNNER_DELAY','severity':sev,'title':f'{name} is waiting for a GitHub-hosted runner','detail':f'Queue time: {queue:.0f}s. This is runner capacity, not CRM concurrency.','safe_action':'Do not start duplicate runs; retry once only if the wait exceeds the recovery threshold.'})
  elif status in {'timed_out','timeout'}:
   issues.append({'fingerprint':'WORKFLOW_TIMEOUT','severity':'critical','title':f'{name} timed out','detail':f'Runtime: {dur}.','safe_action':'Compare runtime with the workflow timeout and recent successful baseline.'})
  elif status in {'failure','failed'}:
   issues.append({'fingerprint':'WORKFLOW_FAILURE','severity':'warning','title':f'{name} latest run failed','detail':'This is active because no newer successful run supersedes it.','safe_action':'Inspect the failing step; do not treat older superseded failures as active.'})
  if isinstance(dur,(int,float)) and dur>900:
   issues.append({'fingerprint':'WORKFLOW_SLOWDOWN','severity':'warning','title':f'{name} latest run is unusually slow','detail':f'Runtime: {dur:.0f}s.','safe_action':'Compare with recent successful median before changing configuration.'})
 # Collapse duplicates by fingerprint/title.
 consolidated={}
 for item in issues:
  key=(item.get('fingerprint'),item.get('title'))
  if key not in consolidated:consolidated[key]={**item,'occurrences':0}
  consolidated[key]['occurrences']+=1
 issues=list(consolidated.values())
 durations=[float(r['duration_seconds']) for r in runs if isinstance(r.get('duration_seconds'),(int,float)) and str(r.get('status')).lower()=='success']
 median=round(statistics.median(durations),1) if durations else None
 success=sum(1 for r in runs if str(r.get('status')).lower()=='success'); failed=sum(1 for r in runs if str(r.get('status')).lower() in {'failure','failed','timed_out','timeout'}); completed=success+failed
 success_rate=round((success/completed)*100,1) if completed else None
 q=[float(r['queue_seconds']) for r in runs if isinstance(r.get('queue_seconds'),(int,float))]; avg_queue=round(sum(q)/len(q),1) if q else None
 state='CRITICAL' if any(x.get('severity')=='critical' for x in issues) else ('WARNING' if any(x.get('severity')=='warning' for x in issues) else 'HEALTHY')
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now.isoformat(),'state':state,'workflow_count':len(workflows),'target_workflow_count':4,'single_pages_publisher':len(pages)==1,'pages_publishers':pages,'pages_timeout_minutes':timeout,'queue_safe':'cancel-in-progress: false' in text,'successful_duration_median_seconds':median,'telemetry_runs':len(runs),'success_rate_pct':success_rate,'average_queue_seconds':avg_queue,'successful_runs':success,'failed_runs':failed,'historical_runs':historical,'issues':issues,'workflows':workflows,'repair_policy':{'max_automatic_retries':1,'queue_warning_seconds':300,'queue_critical_seconds':600,'never_force_push':True,'never_change_secrets':True,'never_change_trading':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'GitHub Actions health written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
