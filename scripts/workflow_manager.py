#!/usr/bin/env python3
"""Canonical workflow validation and repair coordinator for CRM."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run_module(module:str,*args:str)->int:
    return subprocess.run([sys.executable,'-m',module,*args],cwd=ROOT).returncode

def validate()->int:
    rc=run_module('scripts.workflow_policy')
    if rc:return rc
    return run_module('scripts.workflow_doctor')

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['validate','doctor'],nargs='?',default='validate'); a=ap.parse_args()
    return validate() if a.action=='validate' else run_module('scripts.workflow_doctor')
if __name__=='__main__': raise SystemExit(main())
