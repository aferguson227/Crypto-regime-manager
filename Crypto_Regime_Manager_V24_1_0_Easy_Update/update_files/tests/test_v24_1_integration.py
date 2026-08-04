from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_discovery_is_in_scheduled_pipeline():
    wrapper=(ROOT/'scripts/multi_coin_sync_backtest.py').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/multi-coin-update.yml').read_text(encoding='utf-8')
    assert 'discovery_run(False)' in wrapper
    assert 'docs/coin_discovery.json' in workflow
    assert 'docs/coin_universe.json' in workflow

def test_discovery_navigation_and_refresh_feedback():
    page=(ROOT/'docs/discovery.html').read_text(encoding='utf-8')
    index=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert 'v24-primary-nav' in page
    assert 'Refresh latest published results' in page
    assert 'Refresh latest published data' in index
    assert 'refreshButton.addEventListener' in index
