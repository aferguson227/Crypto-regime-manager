import json
from pathlib import Path
from scripts.deployment_intelligence_engine import build, EXACT_FIELDS
ROOT=Path(__file__).parents[1]

def test_v324_release_and_command_centre_route():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='40.1.0'
    rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert rel['deployment_recommendations_enabled'] is True
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
    assert any(r['path']=='command_centre.html' and r['primary'] for r in routes)

def test_deployment_intelligence_is_read_only_and_explainable():
    d=build()
    assert d['application_version']=='40.1.0'
    assert d['read_only'] is True and d['manual_approval_required'] is True
    assert d['overall_action'] in {'DEPLOY','MAINTAIN','WAIT'}
    assert d['actions']
    for a in d['actions']:
        assert 0 <= a['confidence'] <= 100
        assert a['action'] in {'DEPLOY_TODAY','KEEP_RUNNING','WAIT'}
        assert 'recommended_settings' in a and 'blocking_reasons' in a

def test_new_deployment_requires_capital_and_exact_settings():
    d=build()
    if d['capital_status']!='COMPLETE':
        assert not d['deploy_today']
    for a in d['actions']:
        if not a['recommended_settings']['complete'] and a['action']!='KEEP_RUNNING':
            assert a['action']=='WAIT'
            assert any('settings' in x.lower() for x in a['blocking_reasons'])

def test_exact_setting_contract_is_explicit():
    assert {'base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale'}.issubset(EXACT_FIELDS)
