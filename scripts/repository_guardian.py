#!/usr/bin/env python3
"""Repository Guardian: prevent generated state from masquerading as source.

The guardian enforces the contract between runtime-output classification and the
material publication profiles. It also classifies the live Git worktree so new
unregistered generated JSON cannot silently become a recurring install blocker.
"""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GP=ROOT/'config/generated_outputs_policy.json'
MP=ROOT/'config/material_change_policy.json'

def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def git_changes():
 r=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True)
 if r.returncode: return []
 out=[]
 for line in r.stdout.splitlines():
  if not line.strip(): continue
  rel=line[3:].strip().replace('\\','/')
  if ' -> ' in rel: rel=rel.split(' -> ',1)[1]
  out.append((line[:2],rel))
 return out

def validate(scan=False):
 gp=load(GP); mp=load(MP)
 runtime=set(gp.get('runtime_generated_patterns') or [])
 snapshots=set(gp.get('tracked_release_snapshots') or [])
 local=set(((mp.get('profiles') or {}).get('local_agent') or {}).get('paths') or [])
 errors=[]
 # Anything the local agent may publish is generated state and must be classified.
 for rel in sorted(local):
  if rel.startswith('docs/') and rel.endswith('.json') and rel not in runtime and rel not in snapshots:
   errors.append(f'Local-agent generated output is unclassified: {rel}')
 if scan:
  for st,rel in git_changes():
   if rel.startswith('docs/') and rel.endswith('.json') and rel not in runtime and rel not in snapshots:
    errors.append(f'Changed docs JSON is not classified: {rel} ({st}). Add it to config/generated_outputs_policy.json as runtime_generated_patterns or tracked_release_snapshots.')
 if errors:
  print('Repository Guardian: ATTENTION')
  for e in errors: print(' -',e)
  return 1
 print(f'Repository Guardian: HEALTHY; runtime={len(runtime)} local-publish={len(local)} scan={scan}')
 return 0

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['validate','scan'],nargs='?',default='validate'); a=ap.parse_args()
 return validate(scan=a.action=='scan')
if __name__=='__main__': raise SystemExit(main())
