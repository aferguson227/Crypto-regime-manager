#!/usr/bin/env python3
"""V61 isolated heavy research worker.

Runs optimisation/walk-forward in a disposable copy of the application so the
15-minute trading/accounting refresh cannot be blocked or have its Git/runtime
state disturbed. Results are exported to CRM_Data and imported by the next fast
Local Agent cycle.
"""
from __future__ import annotations
import os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def ignore(_,names):
 return {n for n in names if n in {'.git','__pycache__','.pytest_cache','diagnostics_logs','diagnostics_exports','engineering_exports'}}
def main():
 base=Path(tempfile.mkdtemp(prefix='crm-research-'))
 try:
  app=base/'source';shutil.copytree(ROOT,app,ignore=ignore)
  print(f'Research worker: isolated source {app}')
  r=subprocess.run([sys.executable,'-m','scripts.research_scheduler'],cwd=app,text=True)
  if r.returncode:return r.returncode
  return subprocess.run([sys.executable,'-m','scripts.research_snapshot_bridge','export','--source',str(app/'docs')],cwd=ROOT,text=True).returncode
 finally:
  shutil.rmtree(base,ignore_errors=True)
if __name__=='__main__':raise SystemExit(main())
