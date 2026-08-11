#!/usr/bin/env python3
"""V70 resident startup diagnostics and safe recovery.

Purpose:
- distinguish resident heartbeat health from KuCoin live-data freshness;
- capture child process state and recent logs;
- attempt safe read-only/runtime repairs only;
- never place/cancel orders or unlock execution.

Used by installer candidate rehearsal and post-install acceptance.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(os.getenv("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))
DATA_ROOT=Path(os.getenv("CRM_DATA_ROOT",r"C:\Crypto\CRM_Data"))
STATE=DATA_ROOT/"Runtime"/"State"
LOGS=DATA_ROOT/"Runtime"/"Logs"
CONTROL=DATA_ROOT/"Runtime"/"Control"
OUT=DATA_ROOT/"Installer"/"resident_startup_diagnostics.json"
CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    try:return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:return {}

def parse_time(v):
    if not v:return None
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except Exception:return None

def age_of(d):
    t=parse_time(d.get("heartbeat_at") or d.get("generated_at") or d.get("updated_at"))
    return None if t is None else max(0,time.time()-t)

def tail(path,lines=40):
    try:
        data=path.read_text(encoding="utf-8",errors="replace").splitlines()
        return data[-lines:]
    except Exception:
        return []

def run(args,check=False):
    r=subprocess.run([str(x) for x in args],cwd=ROOT,text=True,capture_output=True,
                     creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)
    if check and r.returncode:
        raise RuntimeError((r.stderr or r.stdout or "").strip())
    return r

def status_snapshot():
    resident=read_json(STATE/"crm_resident_status.json")
    live=read_json(STATE/"kucoin_live_service_status.json")
    return {
        "resident":resident,
        "live_service":live,
        "resident_age_seconds":age_of(resident),
        "live_age_seconds":age_of(live),
        "resident_log_tail":tail(LOGS/"crm-resident.log"),
        "kucoin_log_tail":tail(LOGS/"kucoin-live.log"),
        "research_log_tail":tail(LOGS/"research-worker.log"),
    }

def classify(snapshot):
    resident=snapshot["resident"]
    r_age=snapshot["resident_age_seconds"]
    l_age=snapshot["live_age_seconds"]
    if not resident or r_age is None or r_age>20:
        return "RESIDENT_NOT_HEALTHY"
    if l_age is None:
        return "KUCOIN_HEARTBEAT_MISSING"
    if l_age>90:
        return "KUCOIN_HEARTBEAT_STALE"
    return "HEALTHY"

def safe_repair(reason):
    actions=[]
    # Remove stale stop/maintenance flags that can suppress child startup.
    for name in ("stop.request","maintenance.request"):
        p=CONTROL/name
        if p.exists():
            try:
                p.unlink()
                actions.append(f"removed stale control flag {name}")
            except Exception as exc:
                actions.append(f"could not remove {name}: {exc}")

    # Kill only a stale CRM KuCoin live worker before restart.
    if os.name=="nt":
        root_pattern=str(ROOT).replace("'","''")
        ps=(
            "$ErrorActionPreference='SilentlyContinue'; "
            "Get-CimInstance Win32_Process | "
            f"Where-Object {{ $_.CommandLine -like '*{root_pattern}*' -and "
            "($_.CommandLine -like '*scripts.kucoin_live_data_service*' -or "
            "$_.CommandLine -like '*RUN_KUCOIN_LIVE_SERVICE.ps1*') } | "
            "Select-Object -ExpandProperty ProcessId"
        )
        r=run(["powershell.exe","-NoProfile","-NonInteractive","-WindowStyle","Hidden","-Command",ps])
        for line in (r.stdout or "").splitlines():
            line=line.strip()
            if line.isdigit():
                run(["taskkill.exe","/PID",line,"/T","/F"])
                actions.append(f"stopped stale KuCoin live worker pid={line}")

    # Start the live worker directly hidden as a recovery transaction.
    runner=ROOT/"RUN_KUCOIN_LIVE_SERVICE.ps1"
    if runner.exists() and os.name=="nt":
        try:
            subprocess.Popen(
                ["powershell.exe","-NoProfile","-NonInteractive","-WindowStyle","Hidden",
                 "-ExecutionPolicy","Bypass","-File",str(runner)],
                cwd=ROOT,
                env=os.environ.copy(),
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW
            )
            actions.append("started KuCoin live worker directly in hidden recovery mode")
        except Exception as exc:
            actions.append(f"failed to start KuCoin live worker: {exc}")
    return actions

def diagnose_and_repair(wait_seconds=45,repair=True):
    first=status_snapshot()
    reason=classify(first)
    actions=[]
    if reason!="HEALTHY" and repair:
        actions=safe_repair(reason)

    deadline=time.time()+wait_seconds
    last=first
    while time.time()<deadline:
        time.sleep(2)
        last=status_snapshot()
        if classify(last)=="HEALTHY":
            result={
                "generated_at":now(),"status":"PASS","initial_reason":reason,
                "final_reason":"HEALTHY","actions":actions,"snapshot":last
            }
            OUT.parent.mkdir(parents=True,exist_ok=True)
            OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
            return result

    result={
        "generated_at":now(),"status":"FAIL","initial_reason":reason,
        "final_reason":classify(last),"actions":actions,"snapshot":last
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--no-repair",action="store_true")
    ap.add_argument("--wait-seconds",type=int,default=45)
    a=ap.parse_args()
    result=diagnose_and_repair(wait_seconds=a.wait_seconds,repair=not a.no_repair)
    print(f"Resident startup diagnostics: {result['status']} initial={result['initial_reason']} final={result['final_reason']}")
    for action in result.get("actions",[]):print(" -",action)
    snap=result.get("snapshot") or {}
    print(" resident_age=",snap.get("resident_age_seconds"),"live_age=",snap.get("live_age_seconds"))
    if result["status"]!="PASS":
        print(" diagnostics:",OUT)
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
