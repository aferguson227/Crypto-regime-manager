from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")
def test_installer_doctor_has_persistent_state_and_report():
    s=t("scripts/installer_doctor.py")
    assert "upgrade_state.json" in s and "installer_doctor_report.json" in s
def test_installer_doctor_uses_python_native_task_return_codes():
    s=t("scripts/installer_doctor.py")
    assert 'subprocess.run' in s
    assert 'task_query' in s and 'task_create' in s and 'task_delete' in s
    assert "NativeCommandError" not in s
def test_installer_doctor_runs_temporary_task_probe():
    s=t("scripts/installer_doctor.py")
    assert "CryptoRegimeManager-InstallerProbe-" in s
    assert "scheduled_task_probe" in s
def test_installer_doctor_safe_repairs_do_not_hide_source_edits():
    s=t("scripts/installer_doctor.py")
    assert "is_eol_only" in s
    assert "blockers.append(line)" in s
def test_standalone_installer_troubleshooter_exists():
    assert (ROOT/"TROUBLESHOOT_INSTALL_V70.cmd").exists()
