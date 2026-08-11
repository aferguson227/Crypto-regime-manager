#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path

BASE=Path(os.getenv("CRM_DATA_ROOT",r"C:\Crypto\CRM_Data"))/"Runtime"
STATE=BASE/"State"/"crm_resident_status.json"
CONTROL=BASE/"Control"
MAINT=CONTROL/"maintenance.request"
STOP=CONTROL/"stop.request"

def status():
    try:return json.loads(STATE.read_text(encoding="utf-8-sig"))
    except:return {"status":"NOT_RUNNING"}

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status");sub.add_parser("enter-maintenance");sub.add_parser("exit-maintenance");sub.add_parser("stop")
    a=ap.parse_args();CONTROL.mkdir(parents=True,exist_ok=True)
    if a.cmd=="enter-maintenance":
        MAINT.write_text(str(time.time()),encoding="utf-8")
        print("CRM resident maintenance requested.")
    elif a.cmd=="exit-maintenance":
        MAINT.unlink(missing_ok=True);STOP.unlink(missing_ok=True)
        print("CRM resident maintenance released.")
    elif a.cmd=="stop":
        STOP.write_text(str(time.time()),encoding="utf-8");print("CRM resident stop requested.")
    else:print(json.dumps(status(),indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
