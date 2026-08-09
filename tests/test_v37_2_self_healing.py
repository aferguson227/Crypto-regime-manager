import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_self_healing_assets_and_guardrails():
 p=json.loads((ROOT/'config/remediation_playbooks.json').read_text(encoding='utf-8'))
 assert p['application_version']=='54.0.0'
 assert 'trading_actions' in p['guardrails']['never_automatic']
 assert (ROOT/'SELF_HEAL_CRM.cmd').exists()
 assert (ROOT/'scripts/self_healing_engine.py').exists()
def test_visual_policy_and_popup():
 policy=json.loads((ROOT/'config/design_policy.json').read_text(encoding='utf-8'))
 assert policy['formatting']['locale']=='en-GB'
 assert (ROOT/'docs/self-healing.js').exists()
 assert (ROOT/'docs/self-healing.css').exists()
 assert 'Startup health assistant' in (ROOT/'docs/self-healing.js').read_text(encoding='utf-8')
def test_build_runs_new_quality_gates():
 s=(ROOT/'build.ps1').read_text(encoding='utf-8')
 assert 'scripts.self_healing_engine' in s
 assert 'scripts.ui_validation_manager' in s
