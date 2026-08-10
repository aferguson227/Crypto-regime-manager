import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_version():assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='62.0.0'
def test_regime_research_has_entry_and_duration_policy():
 t=(ROOT/'scripts/regime_backtest_engine.py').read_text(encoding='utf-8');assert 'qfl_proxy_3' in t and 'open_duration_hours' in t and 'p90_hours' in t
def test_research_policy_penalises_long_open_trades():
 p=json.loads((ROOT/'config/research_policy.json').read_text(encoding='utf-8'));assert p['trade_duration_policy']['preferred_longest_closed_hours']==168;assert p['trade_duration_policy']['reject_open_duration_hours']==720
def test_xbt_alias_used_for_global_btc():
 t=(ROOT/'scripts/global_market_engine.py').read_text(encoding='utf-8');assert 'canonical_asset' in t and 'xbt_normalised_to_btc' in t
def test_freshness_age_is_not_attention():
 t=(ROOT/'scripts/freshness_controller.py').read_text(encoding='utf-8');assert 'ACTION_REQUIRED' in t and "overall='OVERDUE'" in t;assert "'ATTENTION'" not in t
def test_recommended_bots_explain_process_and_duration():
 t=(ROOT/'scripts/recommended_bots_engine.py').read_text(encoding='utf-8');assert 'process_explanation' in t and 'q1_longest_closed_trade_hours' in t and 'q1_ended_with_open_position' in t
def test_background_research_is_local_agent_module():
 t=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8');assert 'scripts.regime_backtest_engine' in t and 'scripts.research_activity_engine' in t
def test_generated_outputs_registered():
 p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'));r=set(p['runtime_generated_patterns']);assert 'docs/regime_backtest_intelligence.json' in r and 'docs/research_activity.json' in r
def test_universal_text_fit():
 t=(ROOT/'docs/design-system.js').read_text(encoding='utf-8');assert 'CRMFitText' in t and 'ResizeObserver' in t
