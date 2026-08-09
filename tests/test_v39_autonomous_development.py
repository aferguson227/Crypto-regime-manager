from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_v39_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='51.0.0'
 assert json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))['release_name']=='KuCoin Historical Research & Universal Responsive UI'
def test_v39_components():
 for p in ['scripts/issue_lifecycle_engine.py','scripts/repository_hygiene_engine.py','scripts/engineering_scheduler.py','config/generated_outputs_policy.json','RUN_ENGINEERING_AUDIT.cmd','PREPARE_RELEASE.cmd','.github/workflows/crm-health-self-heal.yml']:
  assert (ROOT/p).exists(),p
def test_v39_engineering_package_policy():
 s=(ROOT/'scripts/engineering_package.py').read_text(encoding='utf-8')
 assert 'generated_outputs_policy.json' in s
 assert 'generated_output_manager' in s
def test_v39_guardrails():
 e=(ROOT/'scripts/engineering_intelligence_engine.py').read_text(encoding='utf-8')
 assert 'no_trading_changes' in e and 'no_force_push' in e
