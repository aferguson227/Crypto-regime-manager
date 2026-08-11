from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")

def test_health_distinguishes_resident_from_kucoin_freshness():
    s=t("scripts/crm_resident_health.py")
    assert "RESIDENT_OK_KUCOIN_STALE" in s
    assert "RESIDENT_NOT_HEALTHY" in s
    assert "HEALTHY" in s

def test_startup_diagnostics_has_safe_repair_path():
    s=t("scripts/resident_startup_diagnostics.py")
    assert "KUCOIN_HEARTBEAT_STALE" in s
    assert "KUCOIN_HEARTBEAT_MISSING" in s
    assert "RUN_KUCOIN_LIVE_SERVICE.ps1" in s
    assert "started KuCoin live worker directly in hidden recovery mode" in s

def test_startup_diagnostics_does_not_unlock_execution():
    s=t("scripts/resident_startup_diagnostics.py").lower()
    forbidden=("create_order","cancel_order","place_order","native_execution_gateway")
    assert not any(x in s for x in forbidden)
