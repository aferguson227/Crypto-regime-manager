from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v40_identity_and_policy():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='40.0.0'
    rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
    assert rel['release_name']=='Unified Core Managers'
    p=json.loads((ROOT/'config/core_managers_policy.json').read_text(encoding='utf-8'))
    assert p['principles']['single_authoritative_implementation'] is True

def test_generated_output_manager_is_tracked_safe():
    text=(ROOT/'scripts/generated_output_manager.py').read_text(encoding='utf-8')
    assert "ls-files','--error-unmatch" in text
    assert 'if not tracked(rel): return False' in text
    assert "git','restore','--worktree" in text

def test_build_uses_shared_managers_and_no_blind_restore():
    text=(ROOT/'build.ps1').read_text(encoding='utf-8-sig')
    assert 'scripts.generated_output_manager' in text
    assert 'scripts.workflow_manager' in text
    assert 'scripts.release_manager' in text
    assert 'scripts.diagnostics_manager' in text
    assert 'scripts.ui_validation_manager' in text
    assert "git -C $ProjectPath restore --worktree" not in text

def test_core_managers_exist():
    for rel in ['scripts/generated_output_manager.py','scripts/workflow_manager.py','scripts/release_manager.py','scripts/diagnostics_manager.py','scripts/ui_validation_manager.py']:
        assert (ROOT/rel).exists()
