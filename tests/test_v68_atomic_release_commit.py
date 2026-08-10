import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_atomic_barrier_framework_present():
 t=(ROOT/"scripts/installer_preflight.py").read_text(encoding="utf-8")
 assert "def atomic_release_barrier" in t and "stop_writers()" in t and "clean_runtime()" in t
def test_runtime_policy_covers_race_files():
 p=json.loads((ROOT/"config/generated_outputs_policy.json").read_text(encoding="utf-8"))
 r=set(p["runtime_generated_patterns"])
 assert "docs/kucoin_fill_ledger.json" in r and "docs/local_agent_status.json" in r
