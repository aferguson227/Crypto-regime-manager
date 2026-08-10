import json
from pathlib import Path
from scripts.recommendation_intelligence_engine import build
ROOT=Path(__file__).parents[1]

def test_v325_release_identity_and_build_system_separation():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='61.0.0'
    rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert rel['version']=='61.0.0' and rel['threecommas_mode']=='read_only'
    assert (ROOT/'build.ps1').exists()

def test_recommendation_intelligence_is_explainable_and_read_only():
    data=build(); assert data['read_only'] is True and data['manual_approval_required'] is True
    assert data['recommendations']
    required={'regime','historical','live_conditions','capital','settings','cross_source_agreement'}
    for rec in data['recommendations']:
        assert rec['recommendation_id'] and 0<=rec['overall_confidence']<=100
        assert rec['risk_level'] in {'LOW','MODERATE','HIGH'}
        assert required=={x['name'] for x in rec['confidence_components']}
        assert rec['explanation'] and 'production_comparison' in rec and 'capital_impact' in rec

def test_unknown_expected_metrics_are_not_invented():
    data=build()
    for rec in data['recommendations']:
        expected=rec['expected_behaviour']
        if expected['expected_roi_pct'] is None:
            assert 'not published' in expected['note'].lower()

def test_golden_contract_matches_runtime():
    contract=json.loads((ROOT/'tests/golden/recommendation_intelligence_contract.json').read_text(encoding='utf-8'))
    data=build()
    assert data['schema_version']==contract['schema_version']
    for rec in data['recommendations']:
        assert rec['action'] in contract['valid_actions']
        assert rec['risk_level'] in contract['valid_risk_levels']
