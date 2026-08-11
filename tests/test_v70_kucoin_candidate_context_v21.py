from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v21_preserves_historical_launcher_contracts():
    s = (ROOT / "RUN_KUCOIN_LIVE_SERVICE.ps1").read_text(encoding="utf-8")
    for key in ("KUCOIN_API_KEY", "KUCOIN_API_SECRET", "KUCOIN_API_PASSPHRASE"):
        assert key in s
    assert "$RuntimeApp" in s
    assert "CRM_Data\\Runtime" in s

def test_v21_candidate_never_switches_to_production_runtime_app():
    s = (ROOT / "RUN_KUCOIN_LIVE_SERVICE.ps1").read_text(encoding="utf-8")
    assert "$IsCandidate" in s
    assert "if ($IsCandidate)" in s
    assert "$RuntimeApp = $Project" in s
    assert "-not $IsCandidate" in s
    assert "$env:CRM_PROJECT_PATH = $Project" in s
