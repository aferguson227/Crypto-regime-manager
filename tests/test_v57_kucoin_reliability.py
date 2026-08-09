from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='57.0.0'

def test_order_collector_is_symbol_aware():
    t=(ROOT/'scripts/kucoin_order_state.py').read_text(encoding='utf-8')
    assert "ACTIVE='/api/v1/hf/orders/active/page'" in t
    assert "'symbol':sym" in t
    assert 'symbols_checked' in t
    assert "fetch(ACTIVE,{})" not in t

def test_fill_collector_is_symbol_aware():
    t=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert "params={'symbol':symbol" in t
    assert 'fetch_symbol_recent' in t
    assert 'symbols_checked' in t

def test_eu_fallback_is_opt_in():
    t=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert 'CRM_KUCOIN_ALLOW_REGION_FALLBACK' in t

def test_shared_scope_keeps_tel_and_uses_live_sources():
    t=(ROOT/'scripts/kucoin_symbol_scope.py').read_text(encoding='utf-8')
    assert "add('TEL')" in t
    assert "kucoin_account.json" in t
    assert "live_portfolio_truth.json" in t
    assert "coin_registry.json" in t

def test_local_agent_has_live_heartbeat():
    t=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert "'heartbeat_at':now()" in t
    assert "'phase':'COMPLETE'" in t
    assert "f'Refreshing {mod}.'" in t

def test_health_uses_recovering_not_duplicate_cascade():
    t=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    assert 'RECOVERING_AUTOMATICALLY' in t
    assert 'and not order_problem' in t
    assert 'KuCoin order monitoring is recovering' in t

def test_dashboard_header_is_not_duplicated():
    h=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert '<h1>Crypto Regime Manager</h1>' in h
    assert 'Trading Dashboard' in h
    assert 'Autonomous Trading Operations Centre' not in h
    assert h.count('Today’s Trading Briefing')==1

def test_execution_status_is_per_capability():
    j=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    for label in ['KuCoin balances','KuCoin orders','KuCoin trade history']:
        assert label in j
    assert 'RECOVERING AUTOMATICALLY' in j

def test_native_live_writes_remain_locked():
    t=(ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
    assert 'LIVE ORDER LOCK' in t
