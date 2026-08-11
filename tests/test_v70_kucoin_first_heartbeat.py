from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")
def test_first_heartbeat_requires_fresh_runtime_write():
 s=t("scripts/kucoin_first_heartbeat_supervisor.py")
 assert "fresh_kucoin_truth" in s and "runtime_write_seen" in s
 assert "Process creation alone is not considered success" in s
def test_first_heartbeat_report_is_persistent():
 s=t("scripts/kucoin_first_heartbeat_supervisor.py")
 assert "kucoin_first_heartbeat.json" in s
