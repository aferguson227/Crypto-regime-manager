import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v43_pre_release_generated_outputs_are_classified():
    policy = json.loads((ROOT / "config/generated_outputs_policy.json").read_text(encoding="utf-8"))
    classified = set(policy.get("runtime_generated_patterns") or []) | set(policy.get("tracked_release_snapshots") or [])
    required = {
        "docs/account_intelligence.json",
        "docs/adaptive_intelligence.json",
        "docs/configuration_reconciliation.json",
        "docs/market_intelligence.json",
        "docs/outcome_intelligence.json",
        "docs/system_integrity.json",
        "docs/version.json",
        "docs/capital_intelligence.json",
        "docs/operating_state.json",
        "docs/deployment_intelligence.json",
        "docs/recommendation_intelligence.json",
        "docs/portfolio_intelligence.json",
        "docs/cloud_reliability.json",
        "docs/operational_health.json",
        "docs/decision_quality.json",
        "docs/repository_health.json",
        "docs/engineering_health.json",
        "docs/command_state.json",
        "docs/professional_workspace.json",
        "docs/execution_provider_status.json",
        "docs/research_evidence.json",
        "docs/research_pipeline.json",
        "docs/trade_intelligence.json",
        "docs/expansion_readiness.json",
        "docs/recommended_bots.json",
        "docs/decision_inbox.json",
    }
    assert required <= classified, sorted(required - classified)

def test_version_json_is_release_snapshot_not_runtime_noise():
    policy = json.loads((ROOT / "config/generated_outputs_policy.json").read_text(encoding="utf-8"))
    assert "docs/version.json" in set(policy.get("tracked_release_snapshots") or [])

def test_guardian_gives_classification_remedy():
    text = (ROOT / "scripts/repository_guardian.py").read_text(encoding="utf-8")
    assert "generated_outputs_policy.json" in text
