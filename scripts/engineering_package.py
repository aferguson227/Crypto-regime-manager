#!/usr/bin/env python3
"""Create Engineering Package 2.0 and leave tracked generated outputs clean."""
from __future__ import annotations
import argparse,json,subprocess,zipfile
from datetime import datetime
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
NAMES=['diagnostics.json','diagnostics_runtime.json','operational_health.json','issues.json','performance_history.json','self_healing_status.json','remediation_history.json','ui_health.json','visual_issues.json','github_actions_health.json','engineering_health.json','release_readiness.json','decision_quality.json','issue_lifecycle.json','repository_health.json','engineering_schedule.json','professional_workspace.json','command_state.json','threecommas.json','cloud_reliability.json']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default=str(ROOT/'engineering_exports'));ap.add_argument('--keep-generated',action='store_true');a=ap.parse_args();outdir=Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True)
 subprocess.run(['python','-m','scripts.engineering_scheduler','--mode','daily'],cwd=ROOT,check=True)
 stamp=datetime.now().strftime('%Y%m%d-%H%M%S');out=outdir/f'CRM_Engineering_Package_V{application_version()}_{stamp}.zip';manifest={'schema_version':'2.0','application_version':application_version(),'created_at':stamp,'files':[],'purpose':'single evidence package for accelerated CRM development'}
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for n in NAMES:
   p=DOCS/n
   if p.exists():z.write(p,f'docs/{n}');manifest['files'].append(f'docs/{n}')
  for p in [ROOT/'VERSION',ROOT/'app/release.json',ROOT/'config/workflow_policy.json',ROOT/'config/design_policy.json',ROOT/'config/remediation_playbooks.json',ROOT/'config/generated_outputs_policy.json']:
   if p.exists():z.write(p,str(p.relative_to(ROOT)));manifest['files'].append(str(p.relative_to(ROOT)))
  z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
 if not a.keep_generated:
  policy=json.loads((ROOT/'config/generated_outputs_policy.json').read_text())
  for rel in policy.get('runtime_generated_patterns',[]):subprocess.run(['git','restore','--worktree','--',rel],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 print(f'Engineering Package 2.0 created: {out}');return 0
if __name__=='__main__':raise SystemExit(main())
