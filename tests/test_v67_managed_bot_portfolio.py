from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_version():
 assert text('VERSION').strip()=='69.0.0'
def test_paper_trading_is_persistent_and_read_only():
 s=text('scripts/paper_trading_engine.py')
 assert "paper_portfolio.json" in s
 assert "state_dir()" in s and "paper_trading_state.json" in s
 assert "'read_only_exchange':True" in s
 assert "'automatic_live_deployment':False" in s
 assert 'SAFETY_' in s and "'BASE'" in s
def test_live_service_runs_paper_and_managed_portfolio():
 s=text('scripts/kucoin_live_data_service.py')
 assert "'scripts.paper_trading_engine'" in s
 assert "'scripts.managed_bot_portfolio_engine'" in s
 assert 'subprocess.TimeoutExpired' in s
 assert 'heartbeat_at' in s
 assert 'pid_alive' in s
def test_live_price_snapshot_covers_managed_candidates_in_one_request():
 s=text('scripts/kucoin_live_price_engine.py')
 assert '/api/v1/market/allTickers' in s
 assert "dca_deployment_specs.json" in s
 assert "deployment_lifecycle.json" in s
def test_my_bots_ui_and_add_action_exist():
 s=text('docs/unified_dashboard.js')
 assert "crm_my_bots_v1" in s
 assert 'renderManagedBots' in s
 assert 'crm-add-my-bot' in s
 assert 'Paper trading' in s
 html=text('docs/index.html')
 assert '<h2>My Bots</h2>' in html
def test_live_bot_modal_is_not_a_deployment_modal():
 s=text('docs/unified_dashboard.js')
 assert "row.lifecycle_state==='ACTIVE'" in s
 assert 'Current position is already deployed' in s
 assert 'Would CRM select this strategy today?' in s
def test_live_bot_truth_includes_so_and_reserve():
 s=text('scripts/live_portfolio_truth_engine.py')
 for token in ["'completed_safety_orders'","'max_safety_orders'","'active_safety_orders'","'remaining_dca_reserve_quote'","'average_entry'"]:
  assert token in s
def test_portfolio_allocator_uses_paper_evidence_but_keeps_safety_gate():
 s=text('scripts/portfolio_allocation_engine.py')
 assert "paper_forward_open_pnl_pct" in s
 assert "paper_forward_closed_deals" in s
 assert "safe_multi_bot_pool_usdt" in s
def test_generic_deployment_blocker_removed():
 s=text('scripts/deployment_lifecycle_engine.py')
 assert "One or more deployment evidence gates are incomplete." not in s
 assert "Evidence still required:" in s
def test_health_uses_runtime_heartbeat_and_hkcu():
 s=text('scripts/local_agent_schedule_health.py')
 assert 'heartbeat_age_minutes' in s
 assert "query_live_startup" in s
 h=text('scripts/crm_health_recovery_engine.py')
 assert "heartbeat_at" in h
 assert "No scheduled-task action is required" in h
def test_native_execution_still_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
