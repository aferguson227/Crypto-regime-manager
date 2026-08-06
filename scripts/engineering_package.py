#!/usr/bin/env python3
"""Create one evidence package for accelerated CRM development."""
from __future__ import annotations
import argparse,json,zipfile
from datetime import datetime
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'
NAMES=['diagnostics.json','diagnostics_runtime.json','operational_health.json','issues.json','performance_history.json','self_healing_status.json','remediation_history.json','ui_health.json','visual_issues.json','github_actions_health.json','engineering_health.json','release_readiness.json','decision_quality.json','professional_workspace.json','command_state.json','threecommas.json','cloud_reliability.json']
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',default=str(ROOT/'engineering_exports')); a=ap.parse_args(); outdir=Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime('%Y%m%d-%H%M%S'); out=outdir/f'CRM_Engineering_Package_V{application_version()}_{stamp}.zip'
 manifest={'application_version':application_version(),'created_at':stamp,'files':[]}
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for n in NAMES:
   p=DOCS/n
   if p.exists():z.write(p,f'docs/{n}');manifest['files'].append(f'docs/{n}')
  for p in [ROOT/'VERSION',ROOT/'app/release.json',ROOT/'config/workflow_policy.json',ROOT/'config/design_policy.json',ROOT/'config/remediation_playbooks.json']:
   if p.exists():z.write(p,str(p.relative_to(ROOT)));manifest['files'].append(str(p.relative_to(ROOT)))
  z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
 print(f'Engineering package created: {out}'); return 0
if __name__=='__main__':raise SystemExit(main())
