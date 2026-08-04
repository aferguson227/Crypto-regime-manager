#!/usr/bin/env python3
"""Run the production replay pipeline, then the research-only discovery scan."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from core.engine import main as engine_main
from core.coin_discovery import run as discovery_run

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    status = engine_main()
    if status != 0:
        return status
    try:
        discovery_run(False)
    except Exception as exc:
        # Preserve the production refresh while publishing an explicit discovery error.
        out = ROOT / "docs" / "coin_discovery.json"
        prior = {}
        try:
            prior = json.loads(out.read_text(encoding="utf-8-sig")) if out.exists() else {}
        except Exception:
            prior = {}
        prior.update({
            "version": "24.1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "research_only",
            "scan_status": "error",
            "scan_error": str(exc),
            "summary": {**(prior.get("summary") or {}), "scan_status": "error"},
        })
        out.write_text(json.dumps(prior, indent=2), encoding="utf-8")
        print(f"Discovery scan warning: {exc}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
