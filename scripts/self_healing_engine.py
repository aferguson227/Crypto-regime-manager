#!/usr/bin/env python3
"""Controlled self-diagnosis and safe remediation for CRM V37.2."""
from __future__ import annotations
import argparse,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; CFG=ROOT/'config'
STATUS=DOCS/'self_healing_status.json'; HISTORY=DOCS/'remediation_history.json'
def load(p,default):
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except Exception:return default
def issue(fid,title,risk,auto,detail,repair,validation):return {'fingerprint':fid,'title':title,'risk':risk,'automatic':auto,'detail':detail,'repair':repair,'validation':validation}
def scan():
 issues=[]; version=application_version()
 runps=ROOT/'RUN_DIAGNOSTICS.ps1'
 if runps.exists() and 'scripts\\diagnostics_engine.py' in runps.read_text(encoding='utf-8-sig'):
  issues.append(issue('DIRECT_SCRIPT_EXECUTION','Diagnostics launcher uses direct script execution','low',True,'Package imports can fail.','Switch launcher to python -m scripts.diagnostics_engine.',['module_import']))
 rt=load(DOCS/'diagnostics_runtime.json',{})
 if rt and rt.get('application_version')!=version:
  issues.append(issue('STALE_RUNTIME_DIAGNOSTICS','Runtime diagnostics version is stale','low',True,f"Found {rt.get('application_version')}; expected {version}.",'Regenerate runtime diagnostics.',['release_metadata']))
 pages=ROOT/'.github/workflows/pages-deploy.yml'; policy=load(CFG/'workflow_policy.json',{})
 if pages.exists():
  text=pages.read_text(encoding='utf-8')
  if 'cancel-in-progress: false' not in text or 'timeout-minutes: 30' not in text:
   issues.append(issue('PAGES_POLICY_DRIFT','Pages deployment policy drift','medium',False,'Pages queue-safe settings differ from approved policy.','Restore approved Pages workflow after approval.',['workflow_policy','tests']))
 tc=load(DOCS/'threecommas.json',{}); ts=tc.get('last_success_at') or tc.get('generated_at')
 if ts:
  try:
   age=(datetime.now(timezone.utc)-datetime.fromisoformat(str(ts).replace('Z','+00:00')).astimezone(timezone.utc)).total_seconds()/3600
   if age>2:issues.append(issue('STALE_THREECOMMAS','3Commas data is stale','low',False,f'Last successful sync was {age:.1f} hours ago.','Trigger the read-only 3Commas workflow.',['endpoint_health','freshness']))
  except Exception:pass
 gh=load(DOCS/'github_actions_health.json',{})
 if gh and gh.get('state') in {'WARNING','CRITICAL'}:
  for row in (gh.get('issues') or [])[:5]:
   issues.append(issue(row.get('fingerprint','GITHUB_ACTIONS_ISSUE'),row.get('title') or 'GitHub Actions issue',row.get('severity','medium'),False,row.get('detail') or 'Workflow requires attention.',row.get('safe_action') or 'Review the latest workflow run.',['workflow_policy','latest_commit_published']))
 ui=load(DOCS/'ui_health.json',{})
 if ui and ui.get('overall',{}).get('state') not in {None,'HEALTHY'}:
  issues.append(issue('UI_POLICY_DRIFT','Interface formatting differs from design policy','medium',False,'One or more pages failed visual consistency checks.','Review and apply proposed shared-design repairs.',['ui_health','ui_consistency']))
 return issues
def apply_safe(issues):
 repaired=[]
 for x in issues:
  if x['fingerprint']=='DIRECT_SCRIPT_EXECUTION':
   p=ROOT/'RUN_DIAGNOSTICS.ps1'; s=p.read_text(encoding='utf-8-sig'); s=s.replace('@("scripts\\diagnostics_engine.py", "--full", "--export")','@("-m", "scripts.diagnostics_engine", "--full", "--export")'); p.write_text(s,encoding='utf-8'); repaired.append(x['fingerprint'])
  elif x['fingerprint']=='STALE_RUNTIME_DIAGNOSTICS':
   r=subprocess.run(['python','-m','scripts.diagnostics_engine','--full'],cwd=ROOT)
   if r.returncode==0:repaired.append(x['fingerprint'])
 return repaired
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--apply-safe',action='store_true'); a=ap.parse_args(); now=datetime.now(timezone.utc).isoformat(); before=scan(); repaired=apply_safe(before) if a.apply_safe else []; after=scan(); state='HEALTHY' if not after else ('REPAIRED' if repaired and len(after)<len(before) else 'ATTENTION')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'state':state,'scan':{'issues_found':len(before),'remaining':len(after),'repaired':len(repaired)},'issues':after,'repairs_applied':repaired,'approval_required':[x for x in after if not x['automatic']],'guardrails':{'read_only_trading':True,'no_secret_changes':True,'no_force_push':True,'manual_approval_required':True}}
 STATUS.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 hist=load(HISTORY,{'schema_version':'1.0','events':[]}); events=hist.get('events',[]); events.append({'at':now,'state':state,'found':len(before),'repaired':repaired,'remaining':[x['fingerprint'] for x in after]}); hist.update(application_version=application_version(),generated_at=now,events=events[-500:]); HISTORY.write_text(json.dumps(hist,indent=2),encoding='utf-8')
 print(f'Self-healing scan: {state}; found={len(before)} repaired={len(repaired)} remaining={len(after)}'); return 0 if state in {'HEALTHY','REPAIRED','ATTENTION'} else 1
if __name__=='__main__':raise SystemExit(main())
