import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v35_release():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='42.0.0'
    release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert release['release_name']=='Autonomous Research & Decision Integrity'

def test_dashboard_answers_five_daily_questions():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    for phrase in ['Which bot?','How much?','Which settings?','Why this decision?','What changed?']:
        assert phrase in html
    assert (ROOT/'docs/professional_workspace.js').exists()
    assert (ROOT/'scripts/professional_workspace_engine.py').exists()

def test_canonical_workflow_policy_is_shared():
    policy=json.loads((ROOT/'config/workflow_policy.json').read_text(encoding='utf-8'))
    assert policy['workflows']['pages']['cancel_in_progress'] is False
    assert policy['workflows']['pages']['deploy_timeout_minutes']==30
    from scripts.workflow_policy import validate
    assert validate()==[]
    diag=(ROOT/'scripts/diagnostics_engine.py').read_text(encoding='utf-8')
    assert 'from scripts.workflow_policy import validate' in diag

def test_single_publisher_and_queue_safe_pages():
    pages=(ROOT/'.github/workflows/pages-deploy.yml').read_text(encoding='utf-8')
    assert 'cancel-in-progress: false' in pages
    assert 'timeout-minutes: 30' in pages
    for name in ['crm-data-refresh.yml','crm-health-self-heal.yml','crm-release-validation.yml']:
        text=(ROOT/'.github/workflows'/name).read_text(encoding='utf-8')
        assert 'actions/deploy-pages' not in text
        assert 'actions/upload-pages-artifact' not in text

def test_cloud_update_uses_runtime_diagnostics_and_workspace():
    text=(ROOT/'scripts/cloud_update.py').read_text(encoding='utf-8')
    assert 'RUNTIME_OUTPUT' in text
    assert 'professional_workspace()' in text
    assert 'import build_report, OUTPUT' not in text
