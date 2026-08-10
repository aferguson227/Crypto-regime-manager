from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def text(p):return (ROOT/p).read_text(encoding='utf-8')

def test_runtime_manager_exists_and_targets_external_crm_data():
 s=text('scripts/runtime_state_manager.py')
 assert "CRM_Data" in s
 assert "Runtime" in s
 assert "State" in s and "App" in s
 assert "publish_to_project" in s

def test_live_service_runs_from_isolated_runtime_app():
 s=text('RUN_KUCOIN_LIVE_SERVICE.ps1')
 assert "scripts.runtime_state_manager prepare" in s
 assert "CRM_Data\\\\Runtime" in s or "CRM_Data\\Runtime" in s

def test_live_service_captures_external_state():
 s=text('scripts/kucoin_live_data_service.py')
 assert "from scripts.runtime_state_manager import import_state,capture" in s
 assert "import_state(ROOT)" in s
 assert "capture(ROOT)" in s

def test_local_agent_is_controlled_publication_bridge():
 s=text('scripts/local_agent.py')
 assert "from scripts.runtime_state_manager import import_state,capture" in s
 assert "import_state(ROOT)" in s
 assert "capture(ROOT)" in s

def test_all_docs_json_are_publication_not_source():
 p=json.loads(text('config/generated_outputs_policy.json'))
 assert p["runtime_state_separation"] is True
 assert p["docs_json_policy"]=="PUBLICATION_SNAPSHOT"
 assert p["docs_json_are_never_source"] is True
 s=text('scripts/generated_output_manager.py')
 assert "docs_json = rel.startswith('docs/')" in s

def test_installer_preflight_understands_publication_json():
 s=text('scripts/installer_preflight.py')
 assert "def is_runtime_or_publication" in s
 assert "rel.startswith('docs/')" in s
