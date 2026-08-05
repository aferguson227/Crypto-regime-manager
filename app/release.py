from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def release_metadata() -> dict[str, Any]:
    return json.loads((ROOT / 'app' / 'release.json').read_text(encoding='utf-8-sig'))

def application_version() -> str:
    return str(release_metadata()['version'])
