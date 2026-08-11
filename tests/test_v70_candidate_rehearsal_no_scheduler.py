from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_candidate_rehearsal_architecture_uses_hidden_process():
    s=(ROOT/"UPDATE_V70.md").read_text(encoding="utf-8")
    assert "hidden subprocess" in s.lower()
    assert "task scheduler" in s.lower()

def test_permanent_resident_still_uses_task_manager():
    s=(ROOT/"scripts/resident_task_manager.py").read_text(encoding="utf-8")
    assert "task_create" in s
    assert "CryptoRegimeManager-ResidentRuntime" in s
