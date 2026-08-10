#!/usr/bin/env python3
"""CRM installer/preflight troubleshooter.

Diagnoses and safely resolves common upgrade blockers:
- background CRM processes rewriting generated docs while an install is running;
- runtime-generated files left modified/staged;
- stale pytest caches and backup-test discovery;
- interrupted Git operations;
- genuine source changes that must not be discarded.

It never discards unclassified source changes automatically.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT=Path(os.environ.get("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))
STATE=Path(os.getenv("LOCALAPPDATA") or str(Path.home()))/"CryptoRegimeManager"
LIVE_LOCK=STATE/"kucoin_live_service.lock"

def run(args,check=False,capture=True):
 return subprocess.run([str(x) for x in args],cwd=ROOT,text=True,capture_output=capture)

def git(*a): return run(["git",*a])

def load_policy():
 p=ROOT/"config/generated_outputs_policy.json"
 try:return json.loads(p.read_text(encoding="utf-8-sig"))
 except:return {}

def runtime_paths():
 return set(load_policy().get("runtime_generated_patterns") or [])

def status_rows():
 r=git("status","--porcelain")
 rows=[]
 for line in (r.stdout or "").splitlines():
  if not line.strip():continue
  rel=line[3:].strip().replace("\\","/")
  if " -> " in rel:rel=rel.split(" -> ",1)[1]
  rows.append((line[:2],rel))
 return rows

def stop_background_writers():
 actions=[]
 if os.name!="nt":return actions
 for name in ["CryptoRegimeManager-LocalAgent","CryptoRegimeManager-ResearchWorker"]:
  r=run(["schtasks.exe","/End","/TN",name])
  actions.append({"action":"stop_task","target":name,"returncode":r.returncode})
 if LIVE_LOCK.exists():
  try:
   pid=int(LIVE_LOCK.read_text().strip() or 0)
   if pid:
    r=run(["taskkill.exe","/PID",str(pid),"/T","/F"])
    actions.append({"action":"stop_live_service","pid":pid,"returncode":r.returncode})
  except Exception as exc:
   actions.append({"action":"stop_live_service","status":"warning","detail":str(exc)})
  try:LIVE_LOCK.unlink()
  except:pass
 return actions

def clear_test_contamination():
 removed=0
 for p in ROOT.rglob("__pycache__"):
  if ".git" not in p.parts:
   shutil.rmtree(p,ignore_errors=True);removed+=1
 for p in ROOT.rglob("*.pyc"):
  try:p.unlink();removed+=1
  except:pass
 return removed

def restore_runtime_only():
 runtime=runtime_paths();restored=[]
 for _,rel in status_rows():
  if rel not in runtime:continue
  tracked=run(["git","ls-files","--error-unmatch","--",rel]).returncode==0
  if tracked:
   run(["git","restore","--staged","--worktree","--",rel]);restored.append(rel)
  else:
   p=ROOT/rel
   if p.is_file():
    try:p.unlink();restored.append(rel)
    except:pass
 return restored

def preflight(auto_fix=True):
 report={"project":str(ROOT),"background_actions":[],"runtime_restored":[],"test_cache_removed":0,
         "source_changes":[],"runtime_changes":[],"conflicts":[],"status":"UNKNOWN"}
 if not (ROOT/".git").exists():
  report["status"]="ERROR";report["error"]="Project is not a Git repository.";return report
 if auto_fix:
  report["background_actions"]=stop_background_writers()
  time.sleep(1.0)
  report["test_cache_removed"]=clear_test_contamination()
  # Repeat because a process may have been inside a final write as it was stopped.
  for _ in range(3):
   restored=restore_runtime_only();report["runtime_restored"].extend(x for x in restored if x not in report["runtime_restored"])
   time.sleep(.4)
 rows=status_rows();runtime=runtime_paths()
 for code,rel in rows:
  if code=="UU" or "U" in code:report["conflicts"].append(rel)
  elif rel in runtime:report["runtime_changes"].append(rel)
  else:report["source_changes"].append(rel)
 if report["conflicts"]:report["status"]="CONFLICT"
 elif report["source_changes"]:report["status"]="SOURCE_CHANGES"
 elif report["runtime_changes"]:report["status"]="RUNTIME_WRITER_ACTIVE"
 else:report["status"]="READY"
 return report

def main():
 fix="--diagnose-only" not in sys.argv
 rep=preflight(fix)
 print(json.dumps(rep,indent=2))
 out=ROOT/"diagnostics_logs"/"installer_preflight.json";out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(rep,indent=2),encoding="utf-8")
 if rep["status"]=="READY":
  print("\nCRM installer preflight: READY")
  return 0
 if rep["status"]=="SOURCE_CHANGES":
  print("\nCRM installer preflight: genuine source/unclassified changes remain; no source file was discarded.")
 elif rep["status"]=="RUNTIME_WRITER_ACTIVE":
  print("\nCRM installer preflight: a background process is still rewriting generated runtime state.")
 else:
  print("\nCRM installer preflight:",rep["status"])
 return 2

if __name__=="__main__":raise SystemExit(main())
