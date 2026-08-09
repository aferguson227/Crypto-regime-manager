import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='51.0.0'

def test_local_agent_never_rebases_generated_state():
    text=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert "git','rebase" not in text
    assert "reset','--hard','origin/main" in text
    assert "unpublished non-runtime" in text.lower()

def test_v47_history_outputs_are_published():
    p=json.loads((ROOT/'config/material_change_policy.json').read_text(encoding='utf-8'))
    rows=set(p['profiles']['local_agent']['paths'])
    for name in ['docs/historical_data_status.json','docs/kucoin_walk_forward.json','docs/research_activity.json','docs/independent_trade_accounting.json']:
        assert name in rows

def test_trade_intelligence_reconstructs_live_fields():
    text=(ROOT/'scripts/trade_intelligence_engine.py').read_text(encoding='utf-8')
    assert "public_price" in text
    assert "infer_entry" in text
    assert "infer_tp" in text
    assert "average entry + live bot TP%" in text

def test_staged_recommendations_use_stable_asset_identity():
    text=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "crm_recommended_bots_v1" in text
    assert "stableAsset" in text
    assert "crm-remove-staged" in text
    assert "Review removal" in text

def test_refresh_button_is_honest():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert ">Refresh view</button>" in html
    assert 'id="staged-bots"' in html

def test_mobile_safe_typography():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert "@media(max-width:600px)" in css
    assert "overflow-wrap:break-word!important" in css
