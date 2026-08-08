from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_v32_1_release_and_diagnostics_assets():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='48.0.0'
    release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert release['diagnostics_engine'] is True
    assert (ROOT/'scripts/diagnostics_engine.py').exists()
    assert (ROOT/'RUN_DIAGNOSTICS.cmd').exists()
    assert (ROOT/'RUN_DIAGNOSTICS.ps1').exists()
    assert (ROOT/'docs/diagnostics.html').exists()
    assert (ROOT/'docs/diagnostics.json').exists()

def test_diagnostics_report_is_healthy_and_read_only():
    report=json.loads((ROOT/'docs/diagnostics.json').read_text(encoding='utf-8'))
    assert report['application_version']=='48.0.0'
    assert report['mode']=='read_only_observability'
    assert report['overall']['state'] in {'healthy','warning','fail'}
    assert report['privacy']['secrets_included'] is False
    ids={c['id']:c for c in report['checks']}
    assert ids['safety.read_only']['status']=='pass'
    assert ids['safety.secrets']['status']=='pass'

def test_diagnostics_route_is_registered():
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
    route=next(r for r in routes if r['path']=='diagnostics.html')
    assert route['primary'] is True
    assert route['category']=='system'
