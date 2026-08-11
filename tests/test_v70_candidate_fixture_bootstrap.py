from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")

def test_fixture_bootstrap_runs_before_pytest_contract():
    s=t("scripts/candidate_fixture_bootstrap.py")
    assert "Fixture consistency preflight: PASS" in s
    assert "test_fixture_migrations" in s

def test_known_outputs_have_owning_engines():
    s=t("scripts/candidate_fixture_bootstrap.py")
    for name in ("diagnostics.json","account_intelligence.json","command_state.json"):
        assert name in s

def test_runtime_snapshots_are_not_bulk_rewritten():
    s=t("scripts/candidate_fixture_bootstrap.py")
    assert 'if cls=="RUNTIME"' in s
    assert "runtime_ignored" in s
