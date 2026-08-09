import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v44_version():
    assert (ROOT / 'VERSION').read_text(encoding='utf-8').strip() == '52.0.0'


def test_autonomous_diagnostics_and_freshness_exist():
    assert (ROOT / 'scripts/autonomous_diagnostics.py').exists()
    assert (ROOT / 'scripts/freshness_controller.py').exists()
    assert (ROOT / 'CRM_CHECK.cmd').exists()


def test_local_agent_target_is_15_minutes():
    text = (ROOT / 'SETUP_LOCAL_AGENT.ps1').read_text(encoding='utf-8')
    assert 'New-TimeSpan -Minutes 15' in text


def test_global_market_does_not_fake_kraken_btc():
    text = (ROOT / 'scripts/global_market_engine.py').read_text(encoding='utf-8')
    assert "'status':'KRAKEN_VALIDATED' if btc_hist else ('KUCOIN_HISTORY_AVAILABLE' if btc_kucoin else 'BUILDING')" in text


def test_profitability_is_historical_not_forecast():
    text = (ROOT / 'scripts/recommended_bots_engine.py').read_text(encoding='utf-8')
    assert 'q1_return_on_max_capital_pct' in text
    assert 'not a future-profit forecast' in text


def test_coin_registry_preserves_sui():
    text = (ROOT / 'scripts/coin_registry_engine.py').read_text(encoding='utf-8')
    assert 'strategies.research' in text


def test_new_outputs_registered():
    p = json.loads((ROOT / 'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    r = set(p['runtime_generated_patterns'])
    for x in [
        'docs/freshness_status.json',
        'docs/autonomous_diagnostics.json',
        'docs/global_market.json',
        'docs/optimisation_queue.json',
        'docs/coin_registry.json',
        'docs/recommendation_timeline.json',
    ]:
        assert x in r


def test_dashboard_has_v44_operations_sections():
    h = (ROOT / 'docs/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'docs/unified_dashboard.js').read_text(encoding='utf-8')
    for x in ['Global market regime', 'Refresh status', 'Coin Registry', 'Recommendation Timeline']:
        assert x in h
    assert 'Suggested initial allocation' in js
    assert 'Q1 validated return' in js


def test_existing_local_agent_schedule_is_upgradable():
    text = (ROOT / 'UPDATE_LOCAL_AGENT_SCHEDULE.ps1').read_text(encoding='utf-8')
    assert 'RepetitionInterval (New-TimeSpan -Minutes 15)' in text
