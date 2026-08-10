from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v401_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='68.0.0'
 rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert rel['release_name']=='KuCoin Historical Research & Universal Responsive UI'

def test_health_uses_material_change_staging():
 w=(ROOT/'.github/workflows/crm-health-self-heal.yml').read_text(encoding='utf-8')
 assert 'scripts.material_change_manager stage --profile health' in w
 assert 'timestamp-only evidence will not create a commit' in w
 assert 'docs/performance_history.json' not in w.split('Publish health evidence only when changed',1)[1]

def test_material_change_policy_ignores_volatile_timestamps():
 p=json.loads((ROOT/'config/material_change_policy.json').read_text(encoding='utf-8'))
 assert 'generated_at' in p['volatile_keys']
 assert p['profiles']['health']['purpose']
 assert (ROOT/'scripts/material_change_manager.py').exists()

def test_synchronization_intelligence_and_ui():
 assert (ROOT/'scripts/synchronization_engine.py').exists()
 assert (ROOT/'config/synchronization_policy.json').exists()
 html=(ROOT/'docs/engineering.html').read_text(encoding='utf-8')
 js=(ROOT/'docs/engineering.js').read_text(encoding='utf-8')
 assert 'System synchronisation' in html
 assert 'synchronization_status.json' in js

def test_pages_verifies_live_version():
 w=(ROOT/'.github/workflows/pages-deploy.yml').read_text(encoding='utf-8')
 assert 'Verify live site version' in w
 assert 'version.json' in w
 assert 'cancel-in-progress: false' in w

def test_data_refresh_reuses_hourly_commit_for_actions_telemetry():
 w=(ROOT/'.github/workflows/crm-data-refresh.yml').read_text(encoding='utf-8')
 assert 'actions: read' in w
 assert 'scripts.github_workflow_telemetry' in w
 assert 'scripts.synchronization_engine' in w
