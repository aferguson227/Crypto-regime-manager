#!/usr/bin/env python3
"""Canonical generated-output lifecycle manager.

Only files explicitly declared in config/generated_outputs_policy.json are eligible.
Tracked runtime outputs may be restored. Untracked runtime outputs are never passed
to ``git restore`` and are left alone unless explicitly requested in future policy.
"""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config/generated_outputs_policy.json'

def policy()->dict:
    return json.loads(POLICY.read_text(encoding='utf-8-sig'))

def tracked(rel:str)->bool:
    return subprocess.run(['git','ls-files','--error-unmatch','--',rel],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def restore_tracked(rel:str)->bool:
    if not tracked(rel): return False
    return subprocess.run(['git','restore','--worktree','--',rel],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def clean()->list[str]:
    restored=[]
    for rel in policy().get('runtime_generated_patterns') or []:
        if restore_tracked(rel): restored.append(rel)
    return restored

def status()->dict:
    items=[]
    for rel in policy().get('runtime_generated_patterns') or []:
        p=ROOT/rel
        items.append({'path':rel,'exists':p.exists(),'tracked':tracked(rel)})
    return {'runtime_outputs':items}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['clean','status'],nargs='?',default='clean'); a=ap.parse_args()
    if a.action=='status':
        print(json.dumps(status(),indent=2)); return 0
    restored=clean(); print(f'Generated-output cleanup complete: {len(restored)} tracked runtime files restored; untracked outputs skipped safely.'); return 0
if __name__=='__main__': raise SystemExit(main())
