#!/usr/bin/env python3
"""Restore tracked runtime-generated outputs without touching source files."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; POLICY=ROOT/'config/generated_outputs_policy.json'

def tracked(rel:str)->bool:
    return subprocess.run(['git','ls-files','--error-unmatch','--',rel],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def clean()->list[str]:
    p=json.loads(POLICY.read_text(encoding='utf-8-sig')); restored=[]
    for rel in p.get('runtime_generated_patterns') or []:
        if tracked(rel):
            r=subprocess.run(['git','restore','--worktree','--',rel],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if r.returncode==0: restored.append(rel)
    return restored

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['clean'],nargs='?',default='clean');a=ap.parse_args()
    restored=clean();print(f'Generated-output cleanup complete: {len(restored)} tracked runtime files restored.');return 0
if __name__=='__main__':raise SystemExit(main())
