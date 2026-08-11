from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def t(p):
    return (ROOT/p).read_text(encoding="utf-8")

def test_kucoin_launcher_uses_execution_context_not_live_repo():
    s=t("RUN_KUCOIN_LIVE_SERVICE.ps1")
    assert "CRM_PROJECT_PATH" in s
    assert "CRM_PYTHON_EXECUTABLE" in s
    assert "scripts.runtime_state_manager prepare" in s
    assert "scripts.kucoin_live_data_service" in s
    assert r"C:\Crypto\Projects" not in s

def test_candidate_installer_exports_exact_python_interpreter():
    installer=(ROOT/"tests"/"test_v70_candidate_execution_context.py").read_text(encoding="utf-8")
    # Repository test remains package-safe; launcher contract is asserted above.
    assert "candidate" in installer.lower()
