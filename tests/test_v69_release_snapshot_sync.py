from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
"docs/version.json","docs/system_integrity.json","docs/diagnostics.json","docs/operating_state.json","docs/capital_intelligence.json","docs/deployment_intelligence.json","docs/recommendation_intelligence.json","docs/outcome_intelligence.json","docs/portfolio_intelligence.json","docs/adaptive_intelligence.json","docs/market_intelligence.json"}
def test_release_snapshot_allowlist_matches_publish_validator():
 p=json.loads((ROOT/"config/generated_outputs_policy.json").read_text(encoding="utf-8"))
 assert set(p["release_identity_snapshots"])==EXPECTED
 assert set(p["tracked_release_snapshots"])==EXPECTED
def test_future_preflight_has_release_snapshot_helper():
 s=(ROOT/"scripts/installer_preflight.py").read_text(encoding="utf-8")
 assert "RELEASE_IDENTITY_SNAPSHOTS" in s and "def is_release_identity_snapshot" in s
