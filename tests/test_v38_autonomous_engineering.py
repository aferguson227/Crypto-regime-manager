from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_v38_identity_and_routes():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='52.0.0'
 release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert release['release_name']=='KuCoin Historical Research & Universal Responsive UI'
 routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
 assert any(r['path']=='engineering.html' for r in routes)
def test_engineering_components_exist():
 for p in ['scripts/github_actions_intelligence_engine.py','scripts/engineering_intelligence_engine.py','scripts/decision_quality_engine.py','scripts/engineering_package.py','docs/engineering.html','docs/engineering.js','docs/engineering.css','GENERATE_ENGINEERING_PACKAGE.cmd']:
  assert (ROOT/p).exists(),p
def test_actions_guardrails():
 text=(ROOT/'.github/workflows/pages-deploy.yml').read_text(encoding='utf-8')
 assert 'cancel-in-progress: false' in text
 assert 'timeout-minutes: 30' in text
 heal=(ROOT/'.github/workflows/crm-health-self-heal.yml').read_text(encoding='utf-8')
 assert 'force' not in heal.lower()
 assert 'scripts.self_healing_engine --apply-safe' in heal
def test_engineering_json_outputs_present():
 for n in ['github_actions_health.json','engineering_health.json','release_readiness.json','decision_quality.json']:
  p=ROOT/'docs'/n
  assert p.exists(),n
  assert json.loads(p.read_text(encoding='utf-8'))['application_version']=='52.0.0'
