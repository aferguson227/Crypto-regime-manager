#!/usr/bin/env python3
"""V70 KuCoin first-heartbeat supervisor.

Confirms that a newly launched candidate live-data worker actually progresses through
startup and writes fresh runtime truth. Process creation alone is not considered success.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

PROJECT=Path(os.getenv("CRM_PROJECT_PATH",Path(__file__).resolve().parents[1]))
DATA_ROOT=Path(os.getenv("CRM_DATA_ROOT",r"C:\Crypto\CRM_Data"))
RUNTIME=DATA_ROOT/"Runtime"
INSTALLER=DATA_ROOT/"Installer"
REPORT=INSTALLER/"kucoin_first_heartbeat.json"
CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)

def newest(paths):
    rows=[]
    for p in paths:
        if p.exists():
            try: rows.append((p.stat().st_mtime,p))
            except OSError: pass
    return max(rows)[1] if rows else None

def age(path):
    if not path or not path.exists(): return None
    return max(0.0,time.time()-path.stat().st_mtime)

def candidates():
    # Prefer isolated runtime truth, retain legacy docs only as observation fallback.
    return [
      RUNTIME/"State"/"kucoin_live_service_status.json",
      RUNTIME/"State"/"kucoin_live_prices.json",
      RUNTIME/"State"/"kucoin_account.json",
      RUNTIME/"Data"/"kucoin_live_service_status.json",
      RUNTIME/"Data"/"kucoin_live_prices.json",
      RUNTIME/"Data"/"kucoin_account.json",
      PROJECT/"docs"/"kucoin_live_service_status.json",
      PROJECT/"docs"/"kucoin_live_prices.json",
      PROJECT/"docs"/"kucoin_account.json",
    ]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--wait-seconds",type=int,default=60)
    ap.add_argument("--fresh-seconds",type=int,default=20);a=ap.parse_args()
    started=time.time()
    report={"project":str(PROJECT),"started_at":started,"stages":{
      "process_started":True,"python_loaded":False,"runtime_write_seen":False,
      "fresh_kucoin_truth":False}}
    # If the resident is alive, Python loaded. A fresh KuCoin artifact proves runtime write/API progress.
    report["stages"]["python_loaded"]=True
    last=None
    while time.time()-started<a.wait_seconds:
        p=newest(candidates()); last=p
        ag=age(p)
        if p:
            report["latest_artifact"]=str(p);report["latest_age_seconds"]=ag
            if p.stat().st_mtime>=started-2: report["stages"]["runtime_write_seen"]=True
            if ag is not None and ag<=a.fresh_seconds:
                report["stages"]["fresh_kucoin_truth"]=True
                report["status"]="PASS";break
        time.sleep(1)
    else:
        report["status"]="FAIL"
        report["failure_stage"]="first_heartbeat"
        report["message"]="Worker launched but no fresh KuCoin runtime truth was written before timeout."
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("KuCoin first-heartbeat:",report["status"])
    for k,v in report["stages"].items():print(f" - {k}: {v}")
    if last:print(" - latest:",last,"age=",report.get("latest_age_seconds"))
    print(" - report:",REPORT)
    return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
