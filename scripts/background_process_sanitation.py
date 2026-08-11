#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path

PROJECT=str(Path(os.getenv("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))).lower()
CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)
KNOWN_MARKERS=(
    "scripts.local_agent",
    "scripts.research_worker",
    "scripts.kucoin_live_data_service",
    "run_local_agent.ps1",
    "run_research_worker.ps1",
    "run_kucoin_live_service.ps1",
    "run_crm_resident.ps1",
    "scripts.crm_resident_runtime",
)
SELF_PID=os.getpid()

def _powershell(script):
    return subprocess.run(
        ["powershell.exe","-NoProfile","-NonInteractive","-WindowStyle","Hidden","-Command",script],
        text=True,capture_output=True,creationflags=CREATE_NO_WINDOW
    )

def discover():
    if os.name!="nt":
        return []
    ps = (
        "$ErrorActionPreference='SilentlyContinue'; "
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,Name,CommandLine | "
        "ConvertTo-Json -Compress"
    )
    r=_powershell(ps)
    if r.returncode!=0 or not (r.stdout or "").strip():
        return []
    try:
        data=json.loads(r.stdout)
        if isinstance(data,dict): data=[data]
        return data if isinstance(data,list) else []
    except Exception:
        return []

def crm_workers():
    rows=[]
    for p in discover():
        try: pid=int(p.get("ProcessId") or 0)
        except Exception: continue
        if not pid or pid==SELF_PID: continue
        cmd=str(p.get("CommandLine") or "").lower()
        if PROJECT not in cmd: continue
        if any(m in cmd for m in KNOWN_MARKERS):
            rows.append({
                "pid":pid,
                "ppid":int(p.get("ParentProcessId") or 0),
                "name":str(p.get("Name") or ""),
                "command_line":str(p.get("CommandLine") or "")
            })
    return rows

def stop_workers(timeout=8):
    stopped=[]
    for row in crm_workers():
        r=subprocess.run(
            ["taskkill.exe","/PID",str(row["pid"]),"/T","/F"],
            text=True,capture_output=True,creationflags=CREATE_NO_WINDOW
        )
        if r.returncode==0:
            stopped.append(row)
    deadline=time.time()+timeout
    while time.time()<deadline:
        if not crm_workers():
            break
        time.sleep(.5)
    return {"stopped":stopped,"remaining":crm_workers()}

def main():
    before=crm_workers()
    result=stop_workers()
    print(f"CRM background sanitation: discovered={len(before)} stopped={len(result['stopped'])} remaining={len(result['remaining'])}")
    for row in result["remaining"]:
        print(f" - remaining pid={row['pid']} {row['name']} {row['command_line'][:140]}")
    return 0 if not result["remaining"] else 1

if __name__=="__main__":
    raise SystemExit(main())
