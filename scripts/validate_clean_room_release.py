#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from scripts.clean_room_release import classify
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
 expected=(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip()
 errors=[];warnings=[]
 release=load(ROOT/"app"/"release.json")
 if str(release.get("version"))!=expected:errors.append("app/release.json version mismatch")
 for p in sorted((ROOT/"docs").glob("*.json")):
  rel=p.relative_to(ROOT).as_posix(); cls=classify(rel)
  try:o=load(p)
  except Exception as exc:errors.append(f"{rel} invalid JSON: {exc}");continue
  reported=(o.get("application_version") or o.get("version")) if isinstance(o,dict) else None
  if cls in {"STRICT_RELEASE","BUILD_GENERATED"} and reported and str(reported)!=expected:
   errors.append(f"{rel}={reported!r}, expected {expected!r}")
  elif cls=="RUNTIME" and reported and str(reported)!=expected:
   warnings.append(f"{rel} runtime producer={reported!r}; not a release gate")
 if warnings:
  print("RUNTIME SNAPSHOTS EXCLUDED FROM RELEASE GATE")
  for w in warnings:print(" -",w)
 if errors:
  print("CLEAN-ROOM RELEASE VALIDATION FAILED")
  for e in errors:print(" -",e)
  return 1
 print(f"Clean-room release validation passed for V{expected}.");return 0
if __name__=="__main__":raise SystemExit(main())
