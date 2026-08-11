from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_idempotency_contract_does_not_depend_on_statement_spacing():
    s=(ROOT/"tests/test_v70_resident_task_setup_idempotent.py").read_text(encoding="utf-8")
    assert 'task_end(TASK);d.task_delete(TASK)' not in s
    assert 'd.task_end(TASK)' in s
    assert 'd.task_delete(TASK)' in s
