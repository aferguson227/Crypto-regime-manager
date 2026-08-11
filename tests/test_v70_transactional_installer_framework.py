from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")
def test_resident_setup_wrapper_has_no_raw_schtasks_logic():
    s=t("SETUP_CRM_RESIDENT.ps1")
    assert "schtasks.exe" not in s
    assert "scripts.resident_task_manager install" in s
def test_resident_task_manager_is_python_native():
    s=t("scripts/resident_task_manager.py")
    assert "task_create" in s and "task_query" in s and "task_run" in s
def test_update_v70_documents_installer_doctor():
    s=t("UPDATE_V70.md")
    assert "Installer Doctor" in s
