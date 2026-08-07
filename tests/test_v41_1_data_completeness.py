import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_kucoin_account_provider_is_read_only():
    text=(ROOT/'scripts/integrations/kucoin_account.py').read_text(encoding='utf-8')
    assert "ALLOWED={('GET','/api/v1/accounts')}" in text
    assert 'orders_enabled\':False' in text or "'orders_enabled':False" in text
    assert 'withdrawals_enabled\':False' in text or "'withdrawals_enabled':False" in text


def test_capital_prefers_direct_kucoin_when_available():
    text=(ROOT/'scripts/capital_intelligence_engine.py').read_text(encoding='utf-8')
    assert "kucoin=load('kucoin_account.json')" in text
    assert 'KuCoin direct read-only account API' in text


def test_dashboard_is_live_vs_recommended_only():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'production vs live vs recommended' not in html.lower()
    assert '<th>Production</th>' not in js
    assert '<th>Live</th><th>Recommended</th><th>Decision</th>' in js


def test_market_breadth_uses_canonical_field():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'market.breadth_score' in js


def test_future_execution_providers_are_disabled():
    cfg=json.loads((ROOT/'config/execution_providers.json').read_text(encoding='utf-8'))
    assert cfg['providers']['hummingbot']['enabled'] is False
    assert cfg['providers']['kucoin_direct_execution']['enabled'] is False
    assert cfg['guardrails']['live_write_enabled'] is False
