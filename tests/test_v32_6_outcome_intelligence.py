import json
from pathlib import Path
from scripts.outcome_intelligence_engine import build, VALID_STATUSES
ROOT=Path(__file__).parents[1]

def test_v326_release_and_outcome_route():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='33.0.3'
    rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert rel['version']=='33.0.3' and rel['threecommas_mode']=='read_only'
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
    assert any(r['path']=='outcome.html' for r in routes)

def test_outcome_engine_is_read_only_and_does_not_invent_results():
    data=build(); assert data['read_only'] is True and data['manual_approval_required'] is True
    for rec in data['records']:
        assert rec['status'] in VALID_STATUSES
        if rec['status']!='COMPLETED':
            assert rec['correct'] is None

def test_outcome_analytics_contract():
    contract=json.loads((ROOT/'tests/golden/outcome_intelligence_contract.json').read_text(encoding='utf-8'))
    data=build(); assert data['schema_version']==contract['schema_version']
    assert set(contract['required_analytics']).issubset(data['analytics'])
    assert {x['status'] for x in data['records']}.issubset(set(contract['valid_statuses']))

def test_confidence_calibration_is_explicitly_unknown_without_judged_outcomes():
    data=build()
    if not data['analytics']['judged_outcomes']:
        assert all(x['observed_accuracy_pct'] is None for x in data['confidence_calibration'])
