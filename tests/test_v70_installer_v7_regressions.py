from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_resident_contract_tests_target_python_manager_not_removed_powershell_helpers():
    s=(ROOT/"tests/test_v70_resident_task_setup_idempotent.py").read_text(encoding="utf-8")
    assert "Test-ScheduledTaskExists" not in s
    assert "Stop-ScheduledTaskIfExists $Task" not in s
    assert "resident_task_manager" in s

def test_setup_wrapper_has_no_ampersand_launcher_dependency():
    # The downloadable Install_V70.cmd is intentionally outside the repository.
    # Repository validation must therefore test the installed recovery wrapper,
    # not assume the package launcher was copied into C:\\Crypto\\Projects.
    s=(ROOT/"SETUP_CRM_RESIDENT.ps1").read_text(encoding="utf-8")
    assert "scripts.resident_task_manager install" in s
    assert "schtasks.exe" not in s
