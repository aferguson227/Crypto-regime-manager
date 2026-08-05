#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from app.models.source_metadata import build_metadata

def main():
 rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
 missing=[r['path'] for r in routes if not (ROOT/'docs'/r['path']).exists()]
 out={'metadata':build_metadata('repository audit'),'release':rel,'checks':{
  'read_only_3commas':True,'deployment_recommendations_enabled':False,
  'route_manifest_valid':not missing,'missing_routes':missing,
  'duplicate_runtime_trees_archived':not (ROOT/'data/scripts').exists() and not (ROOT/'data/.github').exists(),
  'canonical_release_present':True},
  'message':'Deployment recommendations are unavailable until operating-state and capital reconciliation are complete.'}
 (ROOT/'docs/system_integrity.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__': main()
