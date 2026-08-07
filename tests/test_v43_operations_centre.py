import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_decision_inbox_engine_exists_and_is_read_only():
    text=(ROOT/'scripts/decision_inbox_engine.py').read_text(encoding='utf-8')
    assert 'browser_acknowledgement_only' in text
    assert "'live_bot_mutations':False" in text

def test_recommended_bot_engine_never_creates_live_bot():
    text=(ROOT/'scripts/recommended_bots_engine.py').read_text(encoding='utf-8')
    assert "'creates_live_bot':False" in text
    assert "'automatic_live_deployment':False" in text
    assert 'suggested_pilot_usdt' in text

def test_dashboard_has_change_briefing_and_recommended_bots():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'CRM Decision Briefing' in html
    assert 'Recommended Bots' in html
    assert 'Recommendation History' in html
    assert 'crm_v43_acknowledged_events' in js
    assert 'Add to Recommended Bots' in js
    assert 'downloadJson' in js

def test_new_runtime_outputs_are_managed():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    assert 'docs/decision_inbox.json' in p['runtime_generated_patterns']
    assert 'docs/recommended_bots.json' in p['runtime_generated_patterns']

def test_local_agent_builds_operations_centre_outputs():
    text=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert 'scripts.recommended_bots_engine' in text
    assert 'scripts.decision_inbox_engine' in text
