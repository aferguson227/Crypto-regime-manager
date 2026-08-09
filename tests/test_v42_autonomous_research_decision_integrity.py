import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT/'docs'/name).read_text(encoding='utf-8'))

def test_v42_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='57.0.0'

def test_portfolio_does_not_copy_asset_keep_active_to_idle_bots():
    text=(ROOT/'scripts/portfolio_intelligence_engine.py').read_text(encoding='utf-8')
    assert "if active_deals>0:" in text
    assert "action='KEEP_ACTIVE_DEAL'" in text
    assert "action='DISABLED'" in text
    assert "PAUSE_NEW_DEALS" in text

def test_command_state_understands_lifecycle_actions():
    text=(ROOT/'scripts/command_state_engine.py').read_text(encoding='utf-8')
    assert "'KEEP_ACTIVE_DEAL':1" in text
    assert "'KEEP_ENABLED':2" in text
    assert "'PAUSE_NEW_DEALS':3" in text

def test_recommended_settings_keep_live_when_governed_missing():
    text=(ROOT/'scripts/deployment_intelligence_engine.py').read_text(encoding='utf-8')
    assert "CANONICAL_LIVE_GOVERNED_RECOMMENDATION" in text
    assert "evidence[field]='KEEP_LIVE'" in text
    assert "recommended_settings(prod,live)" in text

def test_research_pipeline_is_read_only():
    text=(ROOT/'scripts/research_pipeline_engine.py').read_text(encoding='utf-8')
    assert "'automatic_production_promotion':False" in text
    assert "'manual_approval_required':True" in text
    assert "READY_FOR_MANUAL_REVIEW" in text

def test_market_regime_wrap_guard_present():
    html=(ROOT/'docs/market.html').read_text(encoding='utf-8')
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert '#metrics .metric:first-child' in html
    assert 'word-break:normal' in css
