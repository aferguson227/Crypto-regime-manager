#!/usr/bin/env python3
"""Canonical read-only account and balance completeness assessment."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/"docs"; OUT=DOCS/"account_intelligence.json"
def load(name):
 try:
  x=json.loads((DOCS/name).read_text(encoding="utf-8-sig"));return x if isinstance(x,dict) else {}
 except Exception:return {}
def build():
 three=load("threecommas.json"); accounts=three.get("accounts") or []; rows=[]; total=0.0; free=0.0; total_known=True; free_known=True
 for a in accounts:
  if not isinstance(a,dict):continue
  t=a.get("total_usd_value"); f=a.get("free_usdt"); n=int(a.get("balance_records") or len(a.get("balances") or []))
  if t is None: total_known=False
  else: total+=float(t)
  if f is None: free_known=False
  else: free+=float(f)
  rows.append({"account_id":a.get("account_id"),"name":a.get("name"),"exchange":a.get("exchange_name"),"account_record":"PASS","balance_records":n,"balances_status":"PASS" if n else "EMPTY","total_usd_value":t,"free_usdt":f,"source":a.get("balance_source")})
 status="HEALTHY" if rows and all(x["balances_status"]=="PASS" for x in rows) and total_known and free_known else "PARTIAL" if rows else "UNAVAILABLE"
 missing=[]
 if not rows:missing.append("No account records returned.")
 if rows and any(not x["balance_records"] for x in rows):missing.append("One or more accounts returned no balance rows.")
 if not total_known:missing.append("Exchange equity is incomplete.")
 if not free_known:missing.append("Free USDT is incomplete.")
 generated=datetime.now(timezone.utc).isoformat(); seed=json.dumps({"three":three.get("generated_at"),"rows":rows},sort_keys=True)
 return {"schema_version":"1.0","application_version":application_version(),"generated_at":generated,"snapshot_id":hashlib.sha256(seed.encode()).hexdigest()[:20],"status":status,"read_only":True,"accounts":rows,"account_count":len(rows),"balance_record_count":sum(x["balance_records"] for x in rows),"exchange_total":total if total_known and rows else None,"free_usdt":free if free_known and rows else None,"missing":missing,"endpoint_diagnostics":three.get("endpoint_diagnostics") or {}}
def main():OUT.write_text(json.dumps(build(),indent=2),encoding="utf-8");print(f"Account intelligence written: {OUT}");return 0
if __name__=="__main__":raise SystemExit(main())
