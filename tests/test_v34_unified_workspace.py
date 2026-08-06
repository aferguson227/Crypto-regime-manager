import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v34_release_and_unified_routes():
    assert (ROOT/'VERSION').read_text(encoding="utf-8").strip()=='36.0.0'
    release=json.loads((ROOT/'app/release.json').read_text(encoding="utf-8"))
    assert release['release_name']=='Adaptive Decision Workspace'
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding="utf-8"))['routes']
    primary={r['path'] for r in routes if r.get('primary')}
    assert {'index.html','bots.html','portfolio.html','market.html','cloud_reliability.html','diagnostics.html'} <= primary

def test_dashboard_answers_core_questions_on_one_page():
    html=(ROOT/'docs/index.html').read_text(encoding="utf-8")
    for phrase in ['Which bot should I deploy?','How much should I allocate?','Updated DCA settings','Existing bots']:
        assert phrase in html
    js=(ROOT/'docs/command_centre.js').read_text(encoding="utf-8")
    assert 'asset_allocations' in js
    assert 'TEL holdings are never labelled as USDT' in js

def test_universal_workspace_navigation():
    assert (ROOT/'docs/workspace.css').exists()
    assert (ROOT/'docs/workspace.js').exists()
    for page in (ROOT/'docs').glob('*.html'):
        text=page.read_text(encoding="utf-8")
        assert 'workspace.css' in text, page.name
        assert 'workspace.js' in text, page.name

def test_currency_semantics_are_explicit():
    sync=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding="utf-8")
    assert 'allocated_asset_quantity' in sync
    assert 'capital_used_quote' in sync
    assert 'quote_currency' in sync
    capital=(ROOT/'scripts/capital_intelligence_engine.py').read_text(encoding="utf-8")
    assert "('capital_used_quote','capital_used','bought_volume')" in capital
    assert "payload['asset_allocations']" in capital

def test_live_bot_name_matching_handles_dca_aliases():
    from scripts.deployment_intelligence_engine import best_live_bot
    bots=[{'name':'TEL DCA - Low Volatility'},{'name':'TEL DCA - High Bull'}]
    assert best_live_bot(bots,'TEL Low Volatility Bot','TEL')['name']=='TEL DCA - Low Volatility'
