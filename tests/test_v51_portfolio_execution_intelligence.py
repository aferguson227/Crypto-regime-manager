import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='56.0.0'

def test_kucoin_order_state_is_read_only():
    text=(ROOT/'scripts/kucoin_order_state.py').read_text(encoding='utf-8')
    assert "/api/v1/hf/orders/active" in text
    assert "/api/v1/hf/orders/done" in text
    assert "'write_endpoints_implemented':False" in text
    assert "POST" not in text and "DELETE" not in text

def test_reconciliation_detects_stale_provider_and_blocked_entry():
    text=(ROOT/'scripts/execution_reconciliation_engine.py').read_text(encoding='utf-8')
    assert "PROVIDER_STALE_OPEN" in text
    assert "blocked_next_entry_risk" in text
    assert "KuCoin exchange order/fill evidence overrides stale execution-provider telemetry" in text

def test_capital_excludes_stale_provider_deals():
    text=(ROOT/'scripts/capital_intelligence_engine.py').read_text(encoding='utf-8')
    assert "stale_keys" in text
    assert "provider_stale_deals_excluded" in text

def test_cross_exchange_continuation_preserves_original_result():
    text=(ROOT/'scripts/cross_exchange_continuation_engine.py').read_text(encoding='utf-8')
    assert "Reconstruct frozen Kraken cutoff open position" in text
    assert "original_validation_rewritten':False" in text
    assert "CLOSED_ON_KUCOIN_CONTINUATION" in text

def test_backtest_replay_exposes_open_state_for_continuation():
    text=(ROOT/'scripts/core/backtest_lab.py').read_text(encoding='utf-8')
    assert "'open_state':open_state" in text
    assert "'average_entry':avg" in text
    assert "'target_price':target" in text

def test_coin_lifecycle_execution_truth_precedence():
    text=(ROOT/'scripts/coin_registry_engine.py').read_text(encoding='utf-8')
    assert "LIVE_PRODUCTION" in text
    assert "execution_truth_precedence" in text
    assert "research_continues_while_live" in text

def test_portfolio_allocator_is_multi_bot_and_advisory():
    text=(ROOT/'scripts/portfolio_allocation_engine.py').read_text(encoding='utf-8')
    assert "max_abs_correlation_to_live_bots" in text
    assert "available_new_bot_slots" in text
    assert "'automatic_deployment':False" in text

def test_shadow_execution_never_places_orders():
    text=(ROOT/'scripts/shadow_execution_engine.py').read_text(encoding='utf-8')
    assert "'mode':'SHADOW_ONLY'" in text
    assert "'live_order_endpoints_called':False" in text
    assert "'automatic_execution':False" in text

def test_dashboard_uses_deployment_candidates_and_per_bot_profiles():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "<h2>Deployment Candidates</h2>" in html
    assert "<h2>Research Candidates</h2>" in html
    assert "Live bot settings & regime profiles" in html
    assert "liveBotProfiles" in js
    assert "Ready for review — caution" in js

def test_universal_enum_presentation_barrier():
    text=(ROOT/'docs/design-system.js').read_text(encoding='utf-8')
    assert "universal presentation adapter" in text
    assert "MutationObserver" in text
    assert "CRMFormat.label" in text

def test_new_outputs_classified_runtime():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    rows=set(p.get('runtime_generated_patterns') or [])
    for rel in ['docs/kucoin_order_state.json','docs/execution_reconciliation.json','docs/cross_exchange_continuation.json','docs/live_portfolio_truth.json','docs/live_bot_profiles.json','docs/shadow_execution_plans.json']:
        assert rel in rows
