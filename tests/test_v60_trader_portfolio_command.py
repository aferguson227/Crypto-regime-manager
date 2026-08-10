import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v60_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='68.0.0'

def test_portfolio_is_first_command_surface():
    h=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert '<div class="crm-kicker">LIVE PORTFOLIO</div><h2>Today’s Trading Briefing</h2>' in h
    assert h.index('id="trading-briefing"') < h.index('Deployment Queue')
    assert 'id="live-portfolio"' not in h

def test_capital_headline_has_three_distinct_liquidity_states():
    s=(ROOT/'scripts/capital_intelligence_engine.py').read_text(encoding='utf-8')
    assert "payload['kucoin_cash_available']=free" in s
    assert "payload['active_dca_reserve']=remaining_total" in s
    assert "payload['safe_to_allocate_now']=deployable" in s

def test_dashboard_uses_trader_capital_terms():
    s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    for label in ['Portfolio','Cash','DCA reserve','Deployable now']:
        assert label in s

def test_partial_total_pnl_is_explainable():
    s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'open + realised history building' in s
    assert 'Historical search complete' in (ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')

def test_realised_backfill_has_week_and_eta_progress():
    s=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert "'weeks_checked':checked_weeks" in s
    assert "'total_weeks_target':total_weeks" in s
    assert "'estimated_cycles_remaining'" in s
    assert "'estimated_minutes_remaining'" in s

def test_dca_health_does_not_require_all_sos_to_rest_on_exchange():
    s=(ROOT/'scripts/execution_assurance_engine.py').read_text(encoding='utf-8')
    assert "'DCA order protection'" in s
    assert "'DCA capital reserve'" in s
    assert 'Provider-controlled DCA orders may be staged only when their trigger is reached.' in s

def test_background_recovery_does_not_automatically_block_current_snapshot():
    s=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    assert 'usable_account_snapshot' in s
    assert "'decision_data_usable'" in s
    assert "'background_recovery_only'" in s

def test_keep_active_badge_has_intrinsic_width_contract():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert '.crm-action-pill' in css
    assert 'inline-size:max-content!important' in css
    assert 'flex-grow:0!important' in css
    assert 'hyphens:none!important' in css

def test_empty_secondary_cards_are_hidden_after_render():
    s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'hideEmptySecondaryCards' in s
    assert "const ids=['market','sync','settings','operations','ui-quality','changes']" in s

def test_native_execution_remains_locked():
    s=(ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
    assert 'LIVE ORDER LOCK' in s
