from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]

def release() -> dict[str, Any]:
    return json.loads((ROOT/'app'/'release.json').read_text(encoding='utf-8'))

def build_metadata(source: str, *, observed_at: str|None=None, status: str='fresh', warnings: list[str]|None=None, schema_version: str='1.0') -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    rel = release()
    seed = f"{source}|{observed_at or now}|{rel['version']}"
    return {
      'application_version': rel['version'], 'schema_version': schema_version,
      'generated_at': now, 'observed_at': observed_at or now, 'source': source,
      'source_status': status, 'snapshot_id': hashlib.sha256(seed.encode()).hexdigest()[:16],
      'is_stale': status == 'stale', 'warnings': warnings or []
    }
