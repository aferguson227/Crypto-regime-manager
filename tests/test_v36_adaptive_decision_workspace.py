import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v36_release_identity():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='66.0.0'
    release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert release['release_name']=='KuCoin Historical Research & Universal Responsive UI'

def test_dashboard_is_task_oriented_and_accessible():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    for phrase in ["Today’s Trading Briefing",'Which bot?','How much?','Which settings?','Why this decision?','What changed?']:
        assert phrase in html
    assert 'Refresh' in html
    css=(ROOT/'docs/professional_workspace.css').read_text(encoding='utf-8')
    assert '@media(max-width:600px)' in css

def test_workspace_publishes_briefing_and_readiness():
    text=(ROOT/'scripts/professional_workspace_engine.py').read_text(encoding='utf-8')
    assert "'briefing':brief" in text
    assert "'decision_readiness'" in text
    assert "'next_steps'" in text
    assert "'missing_settings'" in text

def test_permanent_workflow_safeguards_remain():
    pages=(ROOT/'.github/workflows/pages-deploy.yml').read_text(encoding='utf-8')
    assert 'cancel-in-progress: false' in pages
    assert 'timeout-minutes: 30' in pages
    cloud=(ROOT/'scripts/cloud_update.py').read_text(encoding='utf-8')
    assert 'RUNTIME_OUTPUT' in cloud
    assert 'professional_workspace()' in cloud
