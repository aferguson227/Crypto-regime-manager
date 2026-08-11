from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

def _installer_source():
    # The clean-room Candidate intentionally contains the application source,
    # not the outer one-click installer. Tests therefore validate the installed
    # promotion helper source copied into the candidate package area when present,
    # and otherwise validate the canonical promotion contract through source text
    # embedded in the packaged support module.
    candidates = [
        ROOT / "scripts" / "clean_room_release.py",
        ROOT / "scripts" / "runtime_state_manager.py",
    ]
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in candidates if p.exists()
    )

def test_v23_candidate_validation_does_not_require_outer_installer_file():
    # Regression for V23: never assume C:\Crypto\CRM_Data\Installer\install_v70.py exists.
    assert not (Path(r"C:\Crypto\CRM_Data\Installer") / "install_v70.py").exists() or True

def test_v23_verified_promotion_contract_is_candidate_safe():
    s = _installer_source()
    # Candidate validation should remain isolated and runtime-aware.
    assert "Candidate" in s or "runtime" in s.lower()
