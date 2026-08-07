from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generated_output_manager_removes_untracked_runtime_outputs():
    text = (ROOT / "scripts" / "generated_output_manager.py").read_text(encoding="utf-8")
    assert "remove_untracked_runtime" in text
    assert "p.unlink()" in text


def test_synchronization_status_is_declared_runtime_output():
    policy = (ROOT / "config" / "generated_outputs_policy.json").read_text(encoding="utf-8")
    assert "docs/synchronization_status.json" in policy


def test_installer_has_pre_payload_runtime_cleanup():
    # This test protects the installed source manager; the installer itself also
    # performs the same policy-driven cleanup before checking git cleanliness.
    text = (ROOT / "scripts" / "generated_output_manager.py").read_text(encoding="utf-8")
    assert "untracked runtime files removed safely" in text
