from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def text(p):return (ROOT/p).read_text(encoding="utf-8")

def test_v70_resident_runtime_exists():
    s=text("scripts/crm_resident_runtime.py")
    assert "git_in_live_data_path" in s
    assert "PUBLICATION_SECONDS" in s
    assert "LIVE_STALE_SECONDS" in s
    assert "MAINTENANCE" in s

def test_v70_resident_has_no_exchange_write_logic():
    s=text("scripts/crm_resident_runtime.py").lower()
    forbidden=["/api/v1/orders","create_order","cancel_order","place_order"]
    assert not any(x in s for x in forbidden)

def test_v70_setup_disables_legacy_schedulers():
    s=text("SETUP_CRM_RESIDENT.ps1")
    assert "CryptoRegimeManager-LocalAgent" in s
    assert "/DISABLE" in s
    assert "CryptoRegimeManager-ResidentRuntime" in s

def test_v70_runner_is_hidden():
    s=text("RUN_CRM_RESIDENT.cmd")
    assert "-WindowStyle Hidden" in s

def test_v70_health_uses_external_runtime_state():
    s=text("scripts/crm_resident_health.py")
    assert "CRM_Data" in s and "Runtime" in s and "kucoin_live_service_status.json" in s
