#!/usr/bin/env python3
"""Canonical release validation coordinator."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(module:str)->int:
    return subprocess.run([sys.executable,'-m',module],cwd=ROOT).returncode

def validate()->int:
    for module in ('scripts.validate_publish','scripts.validate_release_metadata'):
        rc=run(module)
        if rc:return rc
    print('Unified release validation passed.')
    return 0

def main()->int:
    argparse.ArgumentParser().parse_args(); return validate()
if __name__=='__main__': raise SystemExit(main())
