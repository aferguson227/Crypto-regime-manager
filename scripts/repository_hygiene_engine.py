#!/usr/bin/env python3
"""Repository hygiene and release-package intelligence for CRM V39."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/repository_health.json'
EXCLUDE={'.git','__pycache__','.pytest_cache'}
def size(path):
 try:return path.stat().st_size
 except OSError:return 0
def main():
 backups=[]; generated=[]; large=[]; total=0
 for p in ROOT.rglob('*'):
  if any(x in EXCLUDE for x in p.parts):continue
  if p.is_file():
   n=size(p);total+=n
   rel=str(p.relative_to(ROOT)).replace('\\','/')
   if any(x in p.parts for x in {'.update-backups','.fix-backups'}):backups.append({'path':rel,'bytes':n})
   if n>5_000_000:large.append({'path':rel,'bytes':n})
   if rel.startswith(('diagnostics_exports/','engineering_exports/','diagnostics_logs/')):generated.append({'path':rel,'bytes':n})
 reclaim=sum(x['bytes'] for x in backups+generated)
 issues=[]
 if backups:issues.append({'fingerprint':'HISTORICAL_BACKUPS_IN_WORKTREE','severity':'info','title':'Historical backups are present locally','count':len(backups),'automatic':False,'action':'Exclude them from normal source and release archives; preserve separately.'})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'state':'HEALTHY' if not large else 'WARNING','repository_bytes':total,'release_reclaimable_bytes':reclaim,'historical_backup_files':len(backups),'generated_export_files':len(generated),'large_files':large[:25],'issues':issues,'archive_policy':'lean_by_default','full_archive_available':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Repository health written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
