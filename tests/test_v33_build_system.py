from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_build_system_2_metadata_gate():
    text=(ROOT/'build.ps1').read_text(encoding='utf-8')
    assert 'Build System 2.0' in text
    assert 'validate_release_metadata.py' in text

def test_metadata_validator_exists_and_is_read_only():
    text=(ROOT/'scripts/validate_release_metadata.py').read_text(encoding='utf-8')
    assert 'RELEASE METADATA VALIDATION FAILED' in text
    assert 'POST' not in text and 'DELETE' not in text
