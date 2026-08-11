from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_resident_task_manager_remains_available_for_task_repairs():
    assert (ROOT/"scripts"/"resident_task_manager.py").exists()
    assert (ROOT/"SETUP_CRM_RESIDENT.ps1").exists()
