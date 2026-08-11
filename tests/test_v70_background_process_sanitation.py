from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p): return (ROOT/p).read_text(encoding="utf-8")

def test_sanitation_is_strictly_crm_scoped():
    s=t("scripts/background_process_sanitation.py")
    assert "PROJECT not in cmd" in s
    assert "KNOWN_MARKERS" in s
    assert "taskkill.exe" in s

def test_sanitation_knows_all_v70_background_workers():
    s=t("scripts/background_process_sanitation.py")
    for marker in ("scripts.local_agent","scripts.research_worker","scripts.kucoin_live_data_service","scripts.crm_resident_runtime"):
        assert marker in s

def test_resident_task_manager_owns_legacy_retirement():
    s=t("scripts/resident_task_manager.py")
    assert "CryptoRegimeManager-LocalAgent" in s
    assert "CryptoRegimeManager-ResearchWorker" in s
    assert "d.task_enable(name,False)" in s
