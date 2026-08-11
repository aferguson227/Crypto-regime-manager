import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='70.0.0'

def test_history_manager_is_real_incremental_acquisition():
    text=(ROOT/'scripts/historical_data_manager.py').read_text(encoding='utf-8')
    assert "urllib.request.urlopen" in text
    assert "--sync" in text
    assert "backfill_pages_per_symbol_per_cycle" in text
    assert r'C:\Crypto\CRM_Data' in text

def test_history_is_external_to_git():
    policy=json.loads((ROOT/'config/kucoin_research_policy.json').read_text(encoding='utf-8'))
    assert policy['production_quote']=='USDT'
    assert 'BTC' in policy['experimental_quotes']

def test_kucoin_walk_forward_freezes_before_validation():
    text=(ROOT/'scripts/kucoin_walk_forward_engine.py').read_text(encoding='utf-8')
    assert "training_optimisation_only" in text
    assert "freeze_before_validation" in text
    assert "kraken_used_for_optimisation':False" in text

def test_regime_engine_reads_external_kucoin_cache():
    text=(ROOT/'scripts/regime_backtest_engine.py').read_text(encoding='utf-8')
    assert "external_history_dir" in text
    assert "CRM_REGIME_RESEARCH_MAX_DYNAMIC_ASSETS" in text

def test_local_agent_enables_history_sync():
    text=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert "CRM_KUCOIN_HISTORY_SYNC" in text
    assert "scripts.kucoin_walk_forward_engine" in text

def test_global_market_can_use_kucoin_btc_history():
    text=(ROOT/'scripts/global_market_engine.py').read_text(encoding='utf-8')
    assert "KUCOIN_HISTORY_AVAILABLE" in text
    assert "btc_kucoin" in text

def test_universal_card_aware_typography():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert "--crm-font-value" in css
    assert "container-type:inline-size" in css
    assert "@container (max-width:260px)" in css
