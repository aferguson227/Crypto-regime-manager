from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_pytest_is_scoped_to_canonical_tests_only():
 s=(ROOT/'pytest.ini').read_text(encoding='utf-8')
 assert 'testpaths = tests' in s
 assert 'hotfix_backups' in s
 assert '.fix-backups' in s
 assert '--import-mode=importlib' in s
