import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v24_version_and_discovery_safeguards():
    cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    assert cfg['app']['version'] == '42.0.0'
    discovery = cfg['coin_discovery']
    assert discovery['mode'] == 'research_only'
    assert discovery['automatic_add_to_production'] is False
    assert discovery['automatic_3commas_changes'] is False
    assert discovery['research_limits']['manual_approval_required'] is True


def test_timeline_has_return_navigation():
    html = (ROOT / 'docs' / 'timeline.html').read_text(encoding='utf-8')
    assert 'design-system.js' in html
    assert 'v24-dashboard-home' in html


def test_discovery_page_and_scanner_exist():
    html = (ROOT / 'docs' / 'discovery.html').read_text(encoding='utf-8')
    assert 'RESEARCH ONLY' in html
    assert 'automatic' not in html.lower() or 'cannot add coins to production' in html
    assert (ROOT / 'scripts' / 'core' / 'coin_discovery.py').exists()
    assert (ROOT / 'docs' / 'coin_discovery.json').exists()


def test_all_major_pages_have_dashboard_escape_route():
    for name in ['timeline.html','integrity.html','explainability.html','research_queue.html','discovery.html']:
        html = (ROOT / 'docs' / name).read_text(encoding='utf-8')
        assert 'href="index.html"' in html, name
