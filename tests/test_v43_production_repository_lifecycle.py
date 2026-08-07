import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_rec_history_and_research_pipeline_are_runtime():
 p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
 runtime=set(p['runtime_generated_patterns'])
 assert 'docs/recommendation_history.json' in runtime
 assert 'docs/research_pipeline.json' in runtime

def test_local_agent_material_profile_persists_meaningful_history():
 p=json.loads((ROOT/'config/material_change_policy.json').read_text(encoding='utf-8'))
 paths=set(p['profiles']['local_agent']['paths'])
 assert 'docs/recommendation_history.json' in paths
 assert 'docs/research_pipeline.json' in paths

def test_local_agent_cleans_after_publish():
 text=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
 assert "if p.returncode==0:" in text
 assert 'clean_generated()' in text

def test_repository_guardian_exists_and_checks_unclassified_json():
 text=(ROOT/'scripts/repository_guardian.py').read_text(encoding='utf-8')
 assert 'Changed docs JSON is not classified' in text
 assert 'Local-agent generated output is unclassified' in text

def test_generated_manager_classifies_worktree():
 text=(ROOT/'scripts/generated_output_manager.py').read_text(encoding='utf-8')
 assert 'classify_git_status' in text
 assert 'GENERATED_RUNTIME' in text
 assert 'SOURCE_OR_UNCLASSIFIED' in text
