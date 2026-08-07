#!/usr/bin/env python3
"""Synchronise release identity fields across current published JSON state.

This changes only release identity metadata. It does not alter trading values,
market observations, timestamps, balances, recommendations or workflow outcomes.
"""
from __future__ import annotations
import json
from pathlib import Path
from app.release import application_version

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def main() -> int:
    version = application_version()
    release = json.loads((ROOT / 'app' / 'release.json').read_text(encoding='utf-8-sig'))
    release_name = str(release.get('release_name') or '')
    changed = 0
    for path in sorted(DOCS.glob('*.json')):
        try:
            value = json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        if not isinstance(value, dict):
            continue
        dirty = False
        if 'application_version' in value and str(value.get('application_version')) != version:
            value['application_version'] = version
            dirty = True
        metadata = value.get('metadata')
        if isinstance(metadata, dict) and 'application_version' in metadata and str(metadata.get('application_version')) != version:
            metadata['application_version'] = version
            dirty = True
        if path.name in {'version.json', 'system_integrity.json', 'command_state.json'} and 'version' in value and str(value.get('version')) != version:
            value['version'] = version
            dirty = True
        if path.name == 'version.json' and 'release_name' in value and str(value.get('release_name')) != release_name:
            value['release_name'] = release_name
            dirty = True
        if path.name == 'command_state.json' and 'release_name' in value and str(value.get('release_name')) != release_name:
            value['release_name'] = release_name
            dirty = True
        if path.name == 'system_integrity.json' and isinstance(value.get('release'), dict):
            if str(value['release'].get('version')) != version:
                value['release']['version'] = version
                dirty = True
            if str(value['release'].get('release_name')) != release_name:
                value['release']['release_name'] = release_name
                dirty = True
        if dirty:
            path.write_text(json.dumps(value, indent=2), encoding='utf-8')
            changed += 1
    print(f'Release identity synchronised for V{version}: {changed} JSON file(s) updated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
