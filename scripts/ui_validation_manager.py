#!/usr/bin/env python3
"""Canonical UI health and consistency coordinator."""
from __future__ import annotations
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    for module in ('scripts.ui_health_engine','scripts.ui_consistency'):
        rc=subprocess.run([sys.executable,'-m',module],cwd=ROOT).returncode
        if rc:return rc
    print('Unified UI validation passed.')
    return 0
if __name__=='__main__':raise SystemExit(main())
