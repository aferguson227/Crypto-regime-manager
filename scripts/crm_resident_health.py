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
 t=epoch(d.get("heartbeat_at") or d.get("generated_at"));return None if t is None else max(0,time.time()-t)
def main():
 resident=read("crm_resident_status.json");live=read("kucoin_live_service_status.json")
 ra=age(resident);la=age(live)
 ok=resident.get("status") in {"LIVE","RECOVERING"} and ra is not None and ra<20 and la is not None and la<90
 print(f"CRM resident: {resident.get('status','NOT_RUNNING')} resident_age={ra if ra is not None else 'unknown'}s live_age={la if la is not None else 'unknown'}s")
 return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())
