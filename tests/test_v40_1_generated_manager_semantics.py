from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_generated_manager_checks_tracking_before_restore():
    text=(ROOT/'scripts/generated_output_manager.py').read_text(encoding='utf-8')
    tracked=text.index('def tracked(rel: str)')
    restore=text.index('def restore_tracked(rel: str)')
    assert tracked < restore
    restore_block=text[restore:text.index('def remove_untracked_runtime', restore)]
    assert 'if not tracked(rel):' in restore_block
    assert "'git', 'restore', '--worktree'" in restore_block

def test_untracked_runtime_outputs_are_removed_safely():
    text=(ROOT/'scripts/generated_output_manager.py').read_text(encoding='utf-8')
    block=text[text.index('def remove_untracked_runtime'):text.index('def clean', text.index('def remove_untracked_runtime'))]
    assert 'if tracked(rel):' in block
    assert 'if not p.is_file():' in block
    assert 'p.unlink()' in block
