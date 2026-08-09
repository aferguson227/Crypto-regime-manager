import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_v329_release_and_market_output():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='52.0.0'
 rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert rel['release_name']=='KuCoin Historical Research & Universal Responsive UI'
 assert (ROOT/'docs/market.html').exists()
 assert (ROOT/'docs/market_intelligence.json').exists()
def test_v329_market_safeguards_and_explainability():
 p=json.loads((ROOT/'docs/market_intelligence.json').read_text(encoding='utf-8'))
 assert p['read_only'] is True and p['manual_approval_required'] is True
 assert 0<=p['regime_confidence_pct']<=100
 assert p['confidence_attribution']
 assert all(x['automatic_action'] is False for x in p['stress_tests'])
def test_v329_routes_and_pipeline():
 routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
 assert any(r['path']=='market.html' for r in routes)
 assert 'market_intelligence_engine' in (ROOT/'scripts/cloud_update.py').read_text(encoding='utf-8')
def test_v329_build_system_12():
 text=(ROOT/'build.ps1').read_text(encoding='utf-8')
 assert 'Build System 2.1' in text
 assert 'scripts.generated_output_manager' in text
 assert '.update-backups/' in (ROOT/'.gitignore').read_text(encoding='utf-8')
