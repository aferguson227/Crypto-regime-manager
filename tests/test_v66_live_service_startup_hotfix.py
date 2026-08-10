from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')
def test_no_admin_live_service_registration():
 s=text('UPDATE_LOCAL_AGENT_SCHEDULE.ps1')
 assert r'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' in s
 assert "Register-ScheduledTask -TaskName $LiveTask" not in s
def test_health_checks_hkcu_startup():
 s=text('scripts/local_agent_schedule_health.py')
 assert 'query_live_startup' in s and 'HKCU per-user startup' in s
def test_recovery_launches_process_directly():
 s=text('scripts/crm_health_recovery_engine.py')
 assert "subprocess.Popen(['powershell.exe'" in s
 assert "schtasks.exe','/Run','/TN','CryptoRegimeManager-LiveDataService" not in s
