#!/usr/bin/env python3
from __future__ import annotations
import json,os,time
from datetime import datetime
from pathlib import Path
BASE=Path(os.getenv("CRM_DATA_ROOT",r"C:\Crypto\CRM_Data"))/"Runtime"/"State"

def read(name):
    try:return json.loads((BASE/name).read_text(encoding="utf-8-sig"))
    except:return {}

def epoch(v):
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except:return None

def age(d):
    t=epoch(d.get("heartbeat_at") or d.get("generated_at"))
    return None if t is None else max(0,time.time()-t)

def main():
    resident=read("crm_resident_status.json")
    live=read("kucoin_live_service_status.json")
    ra=age(resident);la=age(live)

    resident_ok=(resident.get("status") in {"LIVE","RECOVERING"} and ra is not None and ra<20)
    live_ok=(la is not None and la<90)

    if resident_ok and live_ok:
        state="HEALTHY"
        rc=0
    elif resident_ok:
        state="RESIDENT_OK_KUCOIN_STALE"
        rc=2
    else:
        state="RESIDENT_NOT_HEALTHY"
        rc=1

    print(
        f"CRM resident health: {state} "
        f"resident_status={resident.get('status','NOT_RUNNING')} "
        f"resident_age={ra if ra is not None else 'unknown'}s "
        f"kucoin_live_age={la if la is not None else 'unknown'}s"
    )
    return rc

if __name__=="__main__":
    raise SystemExit(main())
