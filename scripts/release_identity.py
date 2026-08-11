from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def version() -> str:
    try:
        v=(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip()
        if v:
            return v
    except Exception:
        pass
    try:
        d=json.loads((ROOT/"app"/"release.json").read_text(encoding="utf-8-sig"))
        return str(d.get("application_version") or d.get("version") or "UNKNOWN")
    except Exception:
        return "UNKNOWN"

def stamp(data: dict) -> dict:
    out=dict(data)
    out["application_version"]=version()
    return out

if __name__=="__main__":
    print(version())
