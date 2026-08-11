from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v22_credentials_file_contract_preserved():
    assert "kucoin_credentials.json" in (ROOT/"RUN_KUCOIN_LIVE_SERVICE.ps1").read_text(encoding="utf-8")
def test_v22_failure_bundle_has_high_value_evidence():
    s=(ROOT/"scripts"/"installer_failure_bundle.py").read_text(encoding="utf-8")
    for x in ("FAILED_INSTALL_","failure_report.json","candidate_pytest",
              "resident_startup_diagnostics.json","kucoin_first_heartbeat.json",
              "git_status","git_head"):
        assert x in s
