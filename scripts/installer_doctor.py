#!/usr/bin/env python3
"""CRM Installer Doctor & Transactional Upgrade primitives (V70+).

This module is deliberately provider-safe:
- no exchange order placement/cancellation;
- no execution-lock changes;
- repairs only known installer/runtime/Git conditions;
- unknown semantic source edits remain hard blockers.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(os.getenv("CRM_PROJECT_PATH", r"C:\Crypto\Projects"))
DATA_ROOT = Path(os.getenv("CRM_DATA_ROOT", r"C:\Crypto\CRM_Data"))
INSTALLER_ROOT = DATA_ROOT/"Installer"
STATE_FILE = INSTALLER_ROOT/"upgrade_state.json"
REPORT_FILE = INSTALLER_ROOT/"installer_doctor_report.json"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

KNOWN_RUNTIME_JSON = {
    "managed_bot_registry.json","regime_backtest_intelligence.json",
    "resolution_state_status.json","portfolio_decision_consistency.json",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def run(args, *, cwd=ROOT, check=False, capture=True):
    args=[str(x) for x in args]
    r=subprocess.run(args,cwd=cwd,text=True,capture_output=capture,
                     creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)
    if check and r.returncode:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(args)}\n{r.stderr or r.stdout}")
    return r

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
    os.replace(tmp,path)

def set_phase(phase, **extra):
    data={}
    try:data=json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
    except Exception:pass
    data.update({"schema_version":"1.0","phase":phase,"updated_at":now(),**extra})
    write_json(STATE_FILE,data)

def git(*args, check=False):
    return run(["git",*args],check=check)

def status_rows():
    r=git("status","--porcelain")
    rows=[]
    for line in (r.stdout or "").splitlines():
        if not line.strip():continue
        code=line[:2]
        rel=line[3:].strip().strip('"').replace("\\","/")
        if " -> " in rel:rel=rel.split(" -> ",1)[1].strip().strip('"')
        rows.append((code,rel,line))
    return rows

def is_runtime(rel):
    return rel.startswith("docs/") and rel.endswith(".json")

def is_eol_only(rel):
    r=run(["git","diff","--quiet","--ignore-space-at-eol","--",rel])
    return r.returncode==0

def task_query(name):
    if os.name!="nt":return {"exists":False,"returncode":0,"detail":"non-Windows"}
    r=run(["schtasks.exe","/Query","/TN",name])
    return {"exists":r.returncode==0,"returncode":r.returncode,
            "detail":(r.stdout or r.stderr or "").strip()[-500:]}

def task_end(name):
    if os.name!="nt":return 0
    if not task_query(name)["exists"]:return 0
    return run(["schtasks.exe","/End","/TN",name]).returncode

def task_enable(name, enabled=True):
    if os.name!="nt":return 0
    if not task_query(name)["exists"]:return 0
    flag="/ENABLE" if enabled else "/DISABLE"
    return run(["schtasks.exe","/Change","/TN",name,flag]).returncode

def task_delete(name):
    if os.name!="nt":return 0
    if not task_query(name)["exists"]:return 0
    return run(["schtasks.exe","/Delete","/TN",name,"/F"]).returncode

def task_run(name):
    if os.name!="nt":return 0
    if not task_query(name)["exists"]:return 1
    return run(["schtasks.exe","/Run","/TN",name]).returncode

def task_create(name, command, *, schedule="ONLOGON"):
    if os.name!="nt":return 0
    args=["schtasks.exe","/Create","/TN",name,"/SC",schedule,"/RL","LIMITED","/TR",command,"/F"]
    if schedule=="ONCE":
        # A harmless future time is required by schtasks /SC ONCE.
        future=datetime.now()+timedelta(minutes=5)
        args += ["/ST",future.strftime("%H:%M")]
    return run(args).returncode

def scheduled_task_probe():
    """Create/query/run/delete a temporary task before touching source history."""
    if os.name!="nt":
        return {"status":"SKIPPED","reason":"non-Windows"}
    name=f"CryptoRegimeManager-InstallerProbe-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    command='cmd.exe /d /c exit 0'
    try:
        rc=task_create(name,command,schedule="ONCE")
        if rc!=0:return {"status":"FAIL","stage":"create","returncode":rc}
        if not task_query(name)["exists"]:
            return {"status":"FAIL","stage":"query"}
        rc=task_run(name)
        if rc!=0:return {"status":"FAIL","stage":"run","returncode":rc}
        return {"status":"PASS"}
    finally:
        task_end(name);task_delete(name)

def safe_repairs():
    """Repair only known generated/runtime/EOL conditions."""
    repaired=[];blockers=[]
    for code,rel,line in status_rows():
        if code=="??":
            if is_runtime(rel) or (rel.startswith("docs/") and Path(rel).name in KNOWN_RUNTIME_JSON):
                try:(ROOT/rel).unlink(missing_ok=True);repaired.append(f"removed untracked runtime {rel}")
                except Exception:blockers.append(line)
            else:blockers.append(line)
            continue
        if "U" in code or "A" in code or "D" in code or "R" in code or "C" in code:
            blockers.append(line);continue
        if is_runtime(rel):
            run(["git","restore","--staged","--worktree","--",rel])
            repaired.append(f"restored runtime {rel}");continue
        if is_eol_only(rel):
            run(["git","restore","--staged","--worktree","--",rel])
            repaired.append(f"restored EOL-only {rel}");continue
        blockers.append(line)
    return repaired,blockers

def preflight(expected_versions=("69.0.0","70.0.0"), repair=True):
    report={"schema_version":"1.0","generated_at":now(),"checks":[],"repairs":[],"ready":False}
    def add(name,status,detail=""):
        report["checks"].append({"name":name,"status":status,"detail":detail})

    add("project_repository","PASS" if (ROOT/".git").exists() else "FAIL",str(ROOT))
    if not (ROOT/".git").exists():
        write_json(REPORT_FILE,report);return report

    try:installed=(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip()
    except Exception:installed=""
    add("installed_version","PASS" if installed in expected_versions else "FAIL",installed or "missing")

    py=sys.executable
    add("python","PASS" if Path(py).exists() else "FAIL",py)
    add("powershell","PASS" if (os.name!="nt" or shutil.which("powershell.exe")) else "FAIL",shutil.which("powershell.exe") or "missing")
    add("task_scheduler","PASS" if (os.name!="nt" or shutil.which("schtasks.exe")) else "FAIL",shutil.which("schtasks.exe") or "missing")
    add("runtime_root","PASS" if DATA_ROOT.exists() else "REPAIRABLE",str(DATA_ROOT))
    try:
        DATA_ROOT.mkdir(parents=True,exist_ok=True)
        test=INSTALLER_ROOT/"write_test.tmp";test.parent.mkdir(parents=True,exist_ok=True)
        test.write_text("ok",encoding="utf-8");test.unlink()
        add("runtime_write_access","PASS",str(INSTALLER_ROOT))
    except Exception as exc:add("runtime_write_access","FAIL",str(exc))

    if repair:
        repaired,blockers=safe_repairs()
        report["repairs"].extend(repaired)
    else:
        blockers=[x[2] for x in status_rows() if not is_runtime(x[1]) and not is_eol_only(x[1])]
    add("semantic_source_tree","PASS" if not blockers else "FAIL","\n".join(blockers[:20]))

    fetch=git("fetch","origin","main")
    add("git_fetch","PASS" if fetch.returncode==0 else "FAIL",(fetch.stderr or fetch.stdout or "")[-500:])
    if fetch.returncode==0:
        local=git("rev-parse","HEAD").stdout.strip()
        remote=git("rev-parse","origin/main").stdout.strip()
        add("git_identity","PASS",f"HEAD={local[:10]} origin/main={remote[:10]}")
    probe=scheduled_task_probe()
    add("scheduled_task_probe",probe.get("status","FAIL"),json.dumps(probe))

    resident=task_query("CryptoRegimeManager-ResidentRuntime")
    add("resident_task","PASS" if resident["exists"] else "EXPECTED_ABSENT",
        "exists" if resident["exists"] else "will be created during V70 completion")

    fatal={"FAIL"}
    report["ready"]=not any(c["status"] in fatal for c in report["checks"])
    write_json(REPORT_FILE,report)
    return report

def print_report(report):
    print("\nCRM INSTALLER DOCTOR")
    for c in report["checks"]:
        print(f"{c['name']:<28} {c['status']:<16} {c.get('detail','')[:120]}")
    if report.get("repairs"):
        print("\nSafe repairs:")
        for r in report["repairs"]:print(" -",r)
    print("\nREADY TO INSTALL" if report.get("ready") else "\nINSTALLER DOCTOR BLOCKED UPGRADE")

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--diagnose-only",action="store_true")
    args=ap.parse_args()
    report=preflight(repair=not args.diagnose_only)
    print_report(report)
    return 0 if report.get("ready") else 1

if __name__=="__main__":
    raise SystemExit(main())
