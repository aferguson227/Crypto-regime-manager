from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_v26_failure_bundle_collects_resident_task_diagnostics():
    s=(ROOT/"scripts"/"installer_failure_bundle.py").read_text(encoding="utf-8")
    assert "resident_task_install_failure.json" in s
