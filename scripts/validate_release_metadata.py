#!/usr/bin/env python3
"""Validate canonical release identity across published current-state documents."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'

def read(path:Path): return json.loads(path.read_text(encoding='utf-8-sig'))

def main()->int:
    expected=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
    release=read(ROOT/'app/release.json')
    expected_name=str(release.get('release_name') or '')
    errors=[]; checked=[]
    for path in sorted(DOCS.glob('*.json')):
        try: value=read(path)
        except Exception: continue
        if not isinstance(value,dict): continue
        candidates=[]
        if 'application_version' in value: candidates.append(('application_version',value.get('application_version')))
        if path.name in {'version.json','system_integrity.json','command_state.json'} and 'version' in value: candidates.append(('version',value.get('version')))
        metadata=value.get('metadata')
        if isinstance(metadata,dict) and 'application_version' in metadata: candidates.append(('metadata.application_version',metadata.get('application_version')))
        for field,actual in candidates:
            checked.append(f'{path.name}:{field}')
            if str(actual)!=expected: errors.append(f'{path.name} {field}={actual!r}, expected {expected!r}')
        name_candidates=[]
        if path.name == 'version.json' and 'release_name' in value: name_candidates.append(('release_name',value.get('release_name')))
        if path.name == 'system_integrity.json' and isinstance(value.get('release'),dict): name_candidates.append(('release.release_name',value['release'].get('release_name')))
        if path.name == 'command_state.json' and 'release_name' in value: name_candidates.append(('release_name',value.get('release_name')))
        for field,actual in name_candidates:
            checked.append(f'{path.name}:{field}')
            if str(actual)!=expected_name: errors.append(f'{path.name} {field}={actual!r}, expected {expected_name!r}')
    if errors:
        print('RELEASE METADATA VALIDATION FAILED')
        for error in errors: print(' -',error)
        return 1
    print(f'Release metadata valid for {expected}: {len(checked)} fields checked.')
    return 0
if __name__=='__main__': raise SystemExit(main())
