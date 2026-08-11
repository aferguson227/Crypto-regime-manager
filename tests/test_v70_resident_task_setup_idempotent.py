from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_resident_task_setup_is_idempotent_via_python_manager():
    wrapper = text("SETUP_CRM_RESIDENT.ps1")
    manager = text("scripts/resident_task_manager.py")
    assert "scripts.resident_task_manager install" in wrapper
    assert "schtasks.exe" not in wrapper
    assert "task_end(TASK)" in manager
    assert "task_delete(TASK)" in manager
    assert "task_create(TASK" in manager
    assert "task_query(TASK)" in manager
    assert "task_run(TASK)" in manager

def test_missing_resident_task_is_not_fatal_on_first_install():
    doctor = text("scripts/installer_doctor.py")
    manager = text("scripts/resident_task_manager.py")
    # Missing tasks are classified by return code and safely ignored by end/delete.
    assert 'return {"exists":r.returncode==0' in doctor
    assert 'if not task_query(name)["exists"]:return 0' in doctor
    assert "d.task_end(TASK)" in manager
    assert "d.task_delete(TASK)" in manager

def test_setup_wrapper_remains_thin_recovery_entrypoint():
    wrapper = text("SETUP_CRM_RESIDENT.ps1")
    assert "$ErrorActionPreference='Stop'" in wrapper
    assert "scripts.crm_resident_health" in wrapper
