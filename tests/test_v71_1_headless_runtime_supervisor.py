from pathlib import Path
from scripts.release_identity import version

ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_reads_version_file():
    assert version()==(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip()

def test_resident_task_uses_pythonw_directly():
    s=(ROOT/"scripts"/"resident_task_manager.py").read_text(encoding="utf-8")
    assert "pythonw_executable" in s
    assert "-m scripts.crm_resident_runtime" in s
    block=s[s.index("def command():"):s.index("\ndef retire_legacy",s.index("def command():"))]
    assert "powershell.exe" not in block

def test_runtime_status_has_no_hardcoded_v70_identity():
    s=(ROOT/"scripts"/"crm_resident_runtime.py").read_text(encoding="utf-8")
    assert '"application_version":"70.0.0"' not in s
    assert "application_version()" in s

def test_generated_state_policy_classifies_known_runtime_files():
    s=(ROOT/"scripts"/"generated_state_policy.py").read_text(encoding="utf-8")
    for name in ("managed_bot_registry.json","portfolio_decision_consistency.json",
                 "regime_backtest_intelligence.json","resolution_state_status.json",
                 "runtime_reliability.json","runtime_reliability_card.json"):
        assert name in s
    assert '"docs/version.json"' in s

def test_manual_resident_launcher_is_hidden_fallback():
    s=(ROOT/"RUN_CRM_RESIDENT.ps1").read_text(encoding="utf-8")
    assert "Start-Process" in s
    assert "-WindowStyle Hidden" in s
