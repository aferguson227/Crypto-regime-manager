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

ALWAYS_RUNTIME={"docs/local_agent_status.json","docs/local_agent_schedule_health.json","docs/kucoin_live_service_status.json","docs/kucoin_live_prices.json"}
def runtime_paths():
 return set(load_policy().get("runtime_generated_patterns") or []) | ALWAYS_RUNTIME

def is_runtime_or_publication(rel):
 rel=str(rel).replace('\\','/').strip().strip('"')
 return rel in runtime_paths() or (rel.startswith('docs/') and rel.endswith('.json'))

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
 restored=[]
 for _,rel in status_rows():
  if not is_runtime_or_publication(rel):continue
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
 rows=status_rows()
 for code,rel in rows:
  if code=="UU" or "U" in code:report["conflicts"].append(rel)
  elif is_runtime_or_publication(rel):report["runtime_changes"].append(rel)
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

def atomic_release_barrier(project, runtime_paths_set, stop_writers, clean_runtime, status_fn, sleep_fn=time.sleep):
 """Reusable atomic staging barrier for future CRM installers."""
 stop_writers();sleep_fn(2);clean_runtime();previous=None
 for _ in range(4):
  source=[]
  for line in [x for x in status_fn().splitlines() if x.strip()]:
   rel=line[3:].strip().strip('"').replace("\\","/")
   if " -> " in rel:rel=rel.split(" -> ",1)[1].strip().strip('"')
   if rel not in runtime_paths_set:source.append(line)
  snap="\n".join(source)
  if not source or snap==previous:return True
  previous=snap;sleep_fn(1)
 raise RuntimeError("Atomic release barrier could not obtain a stable source snapshot.")


def git_source_status(project=ROOT):
 """Return only genuine source changes. All docs JSON is publication/runtime state."""
 r=subprocess.run(
  ['git','status','--porcelain','--','.',':(exclude,glob)docs/**/*.json'],
  cwd=project,text=True,capture_output=True
 )
 if r.returncode:raise RuntimeError('Unable to inspect source-only Git status.')
 return (r.stdout or '').strip()

def clean_publication_json_git_native(project=ROOT):
 """Best-effort cleanup; source safety never depends on docs JSON being clean."""
 subprocess.run(['git','restore','--staged','--worktree','--',':(glob)docs/**/*.json'],
                cwd=project,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['git','clean','-f','--',':(glob)docs/**/*.json'],
                cwd=project,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def build_release_stage_manifest(project=ROOT):
 """Return only source/static files that actually exist for future release staging."""
 project=Path(project);files=[]
 def add_tree(name):
  root=project/name
  if not root.exists():return
  for p in sorted(root.rglob('*')):
   if not p.is_file():continue
   if '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
   files.append(p.relative_to(project).as_posix())
 for name in ('app','config','data','scripts','tests'):add_tree(name)
 for name in ('VERSION','config.json'):
  if (project/name).is_file():files.append(name)
 docs=project/'docs'
 if docs.exists():
  allowed={'.html','.js','.css','.md','.txt'}
  files.extend(p.relative_to(project).as_posix() for p in sorted(docs.rglob('*')) if p.is_file() and p.suffix.lower() in allowed)
 files.extend(p.relative_to(project).as_posix() for p in sorted(project.glob('UPDATE_V*.md')) if p.is_file())
 return list(dict.fromkeys(files))
