import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_version(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='67.0.0'
def test_capital_manager_v2():
 s=(ROOT/'scripts/portfolio_capital_manager_v2.py').read_text(encoding='utf-8')
 assert 'hard_exchange_commitments_usdt' in s and 'safe_multi_bot_pool_usdt' in s and 'worst_case_headroom_usdt' in s
def test_fast_truth_excludes_research():
 s=(ROOT/'scripts/fast_live_truth_engine.py').read_text(encoding='utf-8')
 assert "'research_excluded':True" in s and 'regime_backtest_engine' not in s and 'kucoin_walk_forward_engine' not in s
def test_live_revalidation_never_mutates_mid_trade():
 s=(ROOT/'scripts/live_strategy_revalidation_engine.py').read_text(encoding='utf-8')
 assert "'automatic_mid_trade_setting_change':False" in s and 'KEEP_CURRENT_DEAL_FROZEN' in s
def test_integrity_separation():
 s=(ROOT/'scripts/integrity_guard_engine.py').read_text(encoding='utf-8')
 for x in ['research_integrity','accounting_integrity','execution_readiness']: assert x in s
def test_allocator_uses_multibot_pool():
 s=(ROOT/'scripts/portfolio_allocation_engine.py').read_text(encoding='utf-8')
 assert "cap2.get('safe_multi_bot_pool_usdt')" in s
def test_kraken_diagnostics_are_staged():
 s=(ROOT/'scripts/kraken_validation_evidence_manager.py').read_text(encoding='utf-8')
 for x in ['archive discovery','asset file discovery','format recognition','4h normalisation','persistent write','continuation detection']: assert x in s
def test_new_outputs_classified():
 p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
 for x in ['docs/portfolio_capital_v2.json','docs/integrity_status.json','docs/live_strategy_revalidation.json','docs/fast_live_truth_status.json']: assert x in p['runtime_generated_patterns']
def test_native_execution_remains_locked():
 assert 'LIVE ORDER LOCK' in (ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
