import json
from pathlib import Path
from scripts.operating_state_engine import build

ROOT=Path(__file__).parents[1]

def test_v322_release_and_route():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='68.0.0'
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
    assert any(x['path']=='operating_state.html' and x['primary'] for x in routes)
    assert (ROOT/'docs/operating_state.js').exists()

def test_operating_state_is_read_only_and_canonical():
    state=build()
    assert state['application_version']=='68.0.0'
    assert state['schema_version']=='1.0'
    assert state['read_only'] is True
    assert state['governance']['automatic_live_changes'] is False
    assert state['governance']['manual_approval_required'] is True
    assert state['snapshot_id']
    assert isinstance(state['bot_decisions'],list)

def test_unknown_capital_is_not_invented():
    state=build(); capital=state['capital']
    assert capital['completeness'] in {'partial','complete'}
    if capital['free_available'] is None:
        assert capital['available_after_reserve'] is None
        assert capital['warnings']

def test_operating_state_sources_are_explicit():
    state=build()
    names={x['name'] for x in state['source_states']}
    assert 'KuCoin strategy snapshot' in names
    assert '3Commas live state' in names
    assert 'Configuration reconciliation' in names
