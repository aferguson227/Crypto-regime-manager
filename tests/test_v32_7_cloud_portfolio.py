import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v327_release_and_outputs():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='33.0.3'
 rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert rel['release_name']=='Trading Command Centre - Account Intelligence'
 for name in ('portfolio_intelligence.json','cloud_reliability.json'):
  assert (ROOT/'docs'/name).exists()

def test_v327_threecommas_endpoint_diagnostics_and_read_only():
 text=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding='utf-8')
 assert 'endpoint_diagnostics' in text and 'permission_denied' in text and 'rate_limited' in text
 import re
 assert 'sell_all_to_usd' not in text and 'panic_sell' not in text

def test_v327_workflow_module_execution():
 three=(ROOT/'.github/workflows/threecommas-update.yml').read_text(encoding='utf-8')
 cloud=(ROOT/'.github/workflows/multi-coin-update.yml').read_text(encoding='utf-8')
 assert 'python -m scripts.threecommas_sync' in three
 assert 'python -m scripts.cloud_update' in cloud

def test_v327_routes_and_manual_control():
 routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
 paths={r['path'] for r in routes}
 assert {'portfolio.html','cloud_reliability.html'} <= paths
 p=json.loads((ROOT/'docs/portfolio_intelligence.json').read_text(encoding='utf-8'))
 assert p['read_only'] is True and p['manual_approval_required'] is True
