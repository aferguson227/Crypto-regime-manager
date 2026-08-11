from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def t(p):return (ROOT/p).read_text(encoding="utf-8")

def test_runtime_state_manager_parser_uses_root_parser():
    s=t("scripts/runtime_state_manager.py")
    assert "sub.parse_args()" not in s
    assert ".parse_args()" in s

def test_repair_is_kept_as_upgrade_guard():
    s=t("scripts/runtime_state_manager_repair.py")
    assert "_SubParsersAction" in s
    assert "Runtime state manager parser verification: PASS" in s

def test_first_heartbeat_prefers_runtime_state():
    s=t("scripts/kucoin_first_heartbeat_supervisor.py")
    assert 'RUNTIME/"State"/"kucoin_live_service_status.json"' in s

def test_resident_has_crash_loop_circuit_breaker():
    s=t("scripts/crm_resident_runtime.py")
    assert "circuit_open" in s
    assert "len(self.failure_times)>=3" in s
