import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v33_release_and_command_state_present():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='33.0.0'
    rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert rel['release_name']=='Trading Command Centre'
    assert (ROOT/'docs/command_state.json').exists()

def test_command_state_is_governed_and_read_only():
    state=json.loads((ROOT/'docs/command_state.json').read_text(encoding='utf-8'))
    assert state['application_version']=='33.0.0'
    assert state['read_only'] is True
    assert state['manual_approval_required'] is True
    assert state['mode']=='unified_read_only_trading_command_state'
    assert isinstance(state['priority_queue'],list)

def test_command_state_contains_all_primary_domains():
    state=json.loads((ROOT/'docs/command_state.json').read_text(encoding='utf-8'))
    for key in ('market','portfolio','capital','recommendations','priority_queue','risks','evidence','cloud','health','source_snapshots'):
        assert key in state

def test_command_centre_uses_canonical_state():
    html=(ROOT/'docs/command_centre.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/command_centre.js').read_text(encoding='utf-8')
    assert 'V33.0.0' in html
    assert "fetch('command_state.json'" in js
    assert 'recommendation_intelligence.json' not in js
