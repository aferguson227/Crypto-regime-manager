from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_build_system_files_and_release_gate():
    required = [
        'build.ps1', 'test.ps1', 'package.ps1', 'release.ps1',
        'BUILD_CRM.cmd', 'CREATE_RELEASE.cmd', 'BUILD_SYSTEM.md',
        'build/Invoke-CRMCommand.ps1',
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel
    build = (ROOT / 'build.ps1').read_text(encoding='utf-8')
    package = (ROOT / 'package.ps1').read_text(encoding='utf-8')
    assert "python" in build and "pytest" in build
    assert "validate_publish.py" in build
    assert "diagnostics_engine.py" in build
    assert "Build gate failed; package not created" in package


def test_all_tests_use_explicit_encoding_for_read_text():
    for path in (ROOT / 'tests').glob('test_*.py'):
        text = path.read_text(encoding='utf-8')
        assert ('.read_text' + '()') not in text, path.name
