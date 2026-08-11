#!/usr/bin/env python3
"""Presentation-safe health normalization for V70.

Only downgrades *publication-only* warnings when authoritative local runtime is current.
Never suppresses KuCoin, order, P/L, capital, protection or execution issues.
"""
from __future__ import annotations
import json,os
from pathlib import Path
from scripts.runtime_state_manager import state_dir

ROOT=Path(__file__).resolve().parents[1];STATE=state_dir()

def load(p):
 try:return json.loads(p.read_text(encoding="utf-8-sig"))
 except:return {}

def main():
 c=load(STATE/"portfolio_decision_consistency.json")
 if not c:return 0
 pub=c.get("publication") or {}
 if pub.get("trading_blocker") is not False:return 0
 for name in ("operational_health.json","issues.json"):
  p=STATE/name
  if not p.exists():continue
  d=load(p)
  changed=False
  def walk(x):
   nonlocal changed
   if isinstance(x,dict):
    text=" ".join(str(x.get(k) or "") for k in ("title","name","area","message","detail","plain_english","what_crm_found")).lower()
    if "publication" in text or "website" in text:
     # Never modify objects that also mention a real trading-data fault.
     real=any(w in text for w in ("kucoin","order","fill","p/l","profit","capital","protection","execution"))
     if not real:
      for k in ("status","severity","state"):
       if k in x and str(x[k]).upper() in ("ACTION_REQUIRED","ACTION REQUIRED","FAIL","ATTENTION","ERROR"):
        x[k]="NOTE";changed=True
      x["plain_english"]="Website publication is delayed, but the local resident runtime is current; this does not block live trading."
      x["trading_blocker"]=False;changed=True
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(d)
  if changed:
   tmp=p.with_suffix(".tmp");tmp.write_text(json.dumps(d,indent=2),encoding="utf-8");os.replace(tmp,p)
 return 0
if __name__=="__main__":raise SystemExit(main())
