import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_version(): assert text('VERSION').strip()=='69.0.0'
def test_public_live_price_engine_is_read_only():
 s=text('scripts/kucoin_live_price_engine.py')
 assert '/api/v1/market/allTickers' in s
 assert "'credentials_required':False" in s
 assert "'write_endpoints_implemented':False" in s
def test_live_portfolio_uses_kucoin_mark_to_market():
 s=text('scripts/live_portfolio_truth_engine.py')
 assert 'KUCOIN_LIVE_MARK_TO_MARKET' in s
 assert "'open_pnl_priced_at'" in s
 assert "'open_pnl_price_source'" in s
def test_operational_schedule_is_five_minutes():
 assert 'New-TimeSpan -Minutes 5' in text('UPDATE_LOCAL_AGENT_SCHEDULE.ps1')
 assert 'New-TimeSpan -Minutes 5' in text('SETUP_LOCAL_AGENT.ps1')
def test_terminal_continuation_closes_waiting_loop():
 s=text('scripts/candidate_review_engine.py')
 assert "bool(co.get('terminal'))" in s
 s2=text('scripts/deployment_lifecycle_engine.py')
 assert "bool(cont.get('terminal'))" in s2
def test_capital_unknown_falls_back_to_canonical_pool():
 s=text('scripts/candidate_review_engine.py')
 assert "safe_pool=num(cap2.get('safe_multi_bot_pool_usdt'))" in s
 assert "'suggested_allocation_usdt':(al.get('recommended_allocation_usdt')" in s
def test_canonical_kucoin_suppresses_false_credential_root():
 s=text('scripts/crm_health_recovery_engine.py')
 assert 'canonical_ready' in s
 assert "and not canonical_ready" in s
def test_fast_truth_uses_real_order_module():
 s=text('scripts/fast_live_truth_engine.py')
 assert "'scripts.kucoin_order_state'" in s
 assert 'kucoin_order_state_engine' not in s
def test_dashboard_shows_pnl_timestamp():
 s=text('docs/unified_dashboard.js')
 assert 'live price' in s and 'ageText(liveTruth.open_pnl_priced_at)' in s
def test_native_execution_still_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
