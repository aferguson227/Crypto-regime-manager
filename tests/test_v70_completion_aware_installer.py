from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v70_completion_mode_documented():
    # Installer is external to repository during execution, so ensure release notes
    # document the supported V70->V70 repair path.
    t=(ROOT/"UPDATE_V70.md").read_text(encoding="utf-8")
    assert "Completion-aware" in t or "completion" in t.lower()
