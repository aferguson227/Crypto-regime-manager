import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_local_agent_status_is_runtime():
 p=json.loads((ROOT/"config/generated_outputs_policy.json").read_text(encoding="utf-8"))
 assert "docs/local_agent_status.json" in p["runtime_generated_patterns"]
def test_preflight_invariant_runtime_failsafe():
 t=(ROOT/"scripts/installer_preflight.py").read_text(encoding="utf-8")
 assert "ALWAYS_RUNTIME" in t and '"docs/local_agent_status.json"' in t
