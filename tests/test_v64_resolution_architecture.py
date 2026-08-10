import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_version(): assert text('VERSION').strip()=='69.0.0'
def test_accounting_baseline():
 s=text('scripts/independent_trade_accounting_engine.py')
 assert 'KNOWN_WITH_HISTORICAL_EXCEPTION' in s and "'accounting_baseline':baseline" in s
def test_continuation_v2_terminal_states():
 s=text('scripts/cross_exchange_continuation_engine.py')
 for x in ['resolver_version','UNAVAILABLE_KRAKEN_SOURCE','UNAVAILABLE_KUCOIN_HISTORY','diagnostic_stage','terminal']:
  assert x in s
def test_canonical_kucoin_service():
 s=text('scripts/kucoin_canonical_service.py')
 assert 'secrets_persisted' in s and "'read_only':True" in s and 'KuCoin is authoritative' in s
def test_capital_v2_runs_before_allocator():
 s=text('scripts/local_agent.py')
 assert s.index("'scripts.portfolio_capital_manager_v2'") < s.index("'scripts.portfolio_allocation_engine'")
def test_resolution_cache_persistent():
 s=text('scripts/resolution_state_cache.py')
 assert "terminal_resolutions.json" in s and "CRM_DATA_ROOT" in s
def test_integrity_detects_continuation_contradictions():
 s=text('scripts/integrity_guard_engine.py')
 assert 'pipeline_contradictions' in s
def test_threecommas_is_secondary_ui():
 s=text('docs/unified_dashboard.js')
 assert '3Commas secondary monitor' in s
def test_native_execution_still_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
