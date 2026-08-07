#!/usr/bin/env python3
"""Canonical diagnostics coordinator."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--release-snapshot',action='store_true'); ap.add_argument('--full',action='store_true'); ap.add_argument('--export',action='store_true'); ap.add_argument('--screenshots',action='store_true'); a=ap.parse_args()
    args=[]
    if a.release_snapshot: args.append('--release-snapshot')
    elif a.full: args.append('--full')
    if a.export:args.append('--export')
    if a.screenshots:args.append('--screenshots')
    return subprocess.run([sys.executable,'-m','scripts.diagnostics_engine',*args],cwd=ROOT).returncode
if __name__=='__main__':raise SystemExit(main())
