from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')
def test_version():assert text('VERSION').strip()=='70.0.0'
def test_managed_bot_registry_is_external_runtime_state():
 s=text('scripts/managed_bot_registry.py')
 assert "state_dir()" in s
 assert "managed_bot_registry.json" in s
 assert "migration_seed" in s
def test_dashboard_persists_add_remove_to_local_runtime_api():
 s=text('docs/unified_dashboard.js')
 assert "persistManagedAsset" in s
 assert "http://127.0.0.1:8765/api" in s
 assert "action,asset" in s
def test_local_runtime_api_has_no_trading_write_endpoint():
 s=text('scripts/runtime_local_api.py')
 assert "write_not_supported" in s
 assert "/api/registry" in s
 assert "order" not in s.lower().split("def do_post")[1]
def test_paper_history_migrates_and_is_retained():
 s=text('scripts/paper_trading_engine.py')
 assert "paper_trading_state.json" in s
 assert "legacy" in s
 assert "'recent_trades'" in s
 assert "'history_retention_per_bot':100" in s
def test_paper_performance_ui_exists():
 s=text('docs/unified_dashboard.js')
 for phrase in ["Forward paper performance","Total paper P/L","Win rate","Recent paper trades"]:
  assert phrase in s
def test_direct_runtime_polling_bypasses_publication_lag():
 s=text('docs/unified_dashboard.js')
 assert "refreshDirectRuntime" in s
 assert "setInterval(refreshDirectRuntime,5000)" in s
 assert "Direct local runtime heartbeat" in s
def test_health_prefers_external_runtime_heartbeat():
 s=text('scripts/crm_health_recovery_engine.py')
 assert "def load_runtime" in s and "def newest" in s
 h=text('scripts/local_agent_schedule_health.py')
 assert "state_dir()/'kucoin_live_service_status.json'" in h
def test_registry_is_runtime_generated():
 p=json.loads(text('config/generated_outputs_policy.json'))
 assert "docs/managed_bot_registry.json" in p["runtime_generated_patterns"]
def test_direct_execution_still_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
