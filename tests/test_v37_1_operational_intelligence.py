import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_operational_outputs_exist_and_are_read_only():
    for name in ['operational_health.json','issues.json','performance_history.json']:
        assert (ROOT/'docs'/name).exists()
    d=json.loads((ROOT/'docs'/'operational_health.json').read_text(encoding="utf-8"))
    assert d['application_version']=='58.0.0'
    assert set(d['scores'])=={'system','data','trading','deployment','decision_readiness'}
    assert d['safeguards']['read_only'] is True
    assert d['safeguards']['manual_approval_required'] is True
def test_operational_health_ui():
    html=(ROOT/'docs'/'diagnostics.html').read_text(encoding="utf-8")
    assert 'Operational Health' in html
    assert 'operational_health.json' not in html
    assert 'operational-health.js' in html
    assert 'Dashboard' in html
