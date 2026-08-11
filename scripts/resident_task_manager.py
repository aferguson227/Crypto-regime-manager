#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
from scripts import installer_doctor as d
from scripts.headless_process import pythonw_executable

ROOT=Path(os.getenv("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))
TASK="CryptoRegimeManager-ResidentRuntime"
LEGACY_TASKS=("CryptoRegimeManager-LocalAgent","CryptoRegimeManager-ResearchWorker")

def command():
    # Long-term V71.1 contract: Task Scheduler launches pythonw directly.
    # No persistent PowerShell host window is required for normal CRM runtime.
    pyw=pythonw_executable()
    return f'"{pyw}" -m scripts.crm_resident_runtime'

def retire_legacy():
    for name in LEGACY_TASKS:
        if d.task_query(name)["exists"]:
            d.task_end(name)
            d.task_enable(name,False)

def restore_legacy():
    for name in LEGACY_TASKS:
        if d.task_query(name)["exists"]:
            d.task_enable(name,True)
            d.task_run(name)

def install():
    runner=ROOT/"RUN_CRM_RESIDENT.ps1"
    if not runner.exists():
        raise RuntimeError(f"Missing resident runner: {runner}")
    d.task_end(TASK); d.task_delete(TASK)
    if d.task_create(TASK,command(),schedule="ONLOGON")!=0:
        raise RuntimeError("Could not create resident scheduled task.")
    if not d.task_query(TASK)["exists"]:
        raise RuntimeError("Resident scheduled task creation did not persist.")
    if d.task_run(TASK)!=0:
        raise RuntimeError("Resident scheduled task could not be started.")
    retire_legacy()
    print("Resident scheduled task created and started; legacy schedules retired.")
    return 0

def remove():
    d.task_end(TASK); d.task_delete(TASK)
    print("Resident scheduled task removed if present.")
    return 0

def status():
    q=d.task_query(TASK)
    print("Resident scheduled task:", "PRESENT" if q["exists"] else "ABSENT")
    for name in LEGACY_TASKS:
        print(name+":", "PRESENT" if d.task_query(name)["exists"] else "ABSENT")
    return 0 if q["exists"] else 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("install","remove","status","retire-legacy","restore-legacy"))
    a=ap.parse_args()
    fn={"install":install,"remove":remove,"status":status,
        "retire-legacy":lambda:(retire_legacy() or 0),
        "restore-legacy":lambda:(restore_legacy() or 0)}[a.action]
    return fn()

if __name__=="__main__":
    raise SystemExit(main())
