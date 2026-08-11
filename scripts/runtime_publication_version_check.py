from __future__ import annotations
import json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
POLICY=ROOT/'config'/'publication_version_policy.json'

def version_of(obj):
    return obj.get('application_version') or obj.get('version') or ((obj.get('metadata') or {}).get('application_version'))

def main():
    release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8-sig'))
    current=str(release['version'])
    policy=json.loads(POLICY.read_text(encoding='utf-8-sig'))
    stale=[];current_rows=[];missing=[];newer=[]
    for name in policy.get('runtime_snapshots') or []:
        p=DOCS/name
        if not p.exists():
            missing.append(name);continue
        obj=json.loads(p.read_text(encoding='utf-8-sig'))
        reported=version_of(obj)
        if not reported:
            stale.append((name,'unknown'));continue
        reported=str(reported)
        if reported==current: current_rows.append(name)
        else:
            # A runtime snapshot from a future software version is contradictory
            # and remains a hard error.
            try:
                a=tuple(int(x) for x in reported.split('.'))
                b=tuple(int(x) for x in current.split('.'))
                if a>b:newer.append((name,reported));continue
            except Exception:
                pass
            stale.append((name,reported))
    print(f'Runtime publication version check: release={current}; current={len(current_rows)}; stale={len(stale)}; missing={len(missing)}')
    for name,v in stale:print(f' - REFRESH REQUIRED: docs/{name} snapshot={v}, application={current}')
    for name in missing:print(f' - MISSING RUNTIME SNAPSHOT: docs/{name}')
    if newer:
        for name,v in newer:print(f' - INVALID FUTURE SNAPSHOT: docs/{name} snapshot={v}, application={current}')
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
