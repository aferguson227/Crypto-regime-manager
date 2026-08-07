#!/usr/bin/env python3
"""Create Engineering Package 2.2 and always leave tracked runtime outputs clean."""
from __future__ import annotations
import argparse,json,subprocess,zipfile
from datetime import datetime
from pathlib import Path
from app.release import application_version
from scripts.generated_output_manager import clean
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
NAMES=['diagnostics.json','diagnostics_runtime.json','operational_health.json','issues.json','performance_history.json','self_healing_status.json','remediation_history.json','ui_health.json','visual_issues.json','github_actions_health.json','workflow_history.json','workflow_doctor.json','engineering_health.json','release_readiness.json','decision_quality.json','issue_lifecycle.json','repository_health.json','engineering_schedule.json','professional_workspace.json','command_state.json','threecommas.json','cloud_reliability.json','trade_intelligence.json','expansion_readiness.json','research_pipeline.json','synchronization_status.json']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default=str(ROOT/'engineering_exports'));ap.add_argument('--keep-generated',action='store_true');a=ap.parse_args();outdir=Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True);out=None
 try:
  subprocess.run(['python','-m','scripts.engineering_scheduler','--mode','daily'],cwd=ROOT,check=True)
  stamp=datetime.now().strftime('%Y%m%d-%H%M%S');out=outdir/f'CRM_Engineering_Package_V{application_version()}_{stamp}.zip';manifest={'schema_version':'2.2','application_version':application_version(),'created_at':stamp,'files':[],'purpose':'single evidence package for accelerated CRM development'}
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
   for n in NAMES:
    p=DOCS/n
    if p.exists():z.write(p,f'docs/{n}');manifest['files'].append(f'docs/{n}')
   for p in [ROOT/'VERSION',ROOT/'app/release.json',ROOT/'config/workflow_policy.json',ROOT/'config/design_policy.json',ROOT/'config/remediation_playbooks.json',ROOT/'config/generated_outputs_policy.json',ROOT/'config/material_change_policy.json',ROOT/'config/synchronization_policy.json']:
    if p.exists():z.write(p,str(p.relative_to(ROOT)));manifest['files'].append(str(p.relative_to(ROOT)))
   z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
  print(f'Engineering Package 2.2 created: {out}')
  return 0
 finally:
  if not a.keep_generated: clean()
if __name__=='__main__':raise SystemExit(main())
