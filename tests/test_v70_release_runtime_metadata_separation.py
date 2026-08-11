from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def text(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_v70_release_metadata_separates_runtime_from_release_identity():
    s=text("scripts/validate_release_metadata.py")
    assert "RUNTIME METADATA REFRESH REQUIRED" in s
    assert "refresh required, not a release failure" in s
    assert "claims future runtime application_version" in s
    assert '"version.json"' in s

def test_v70_release_metadata_keeps_core_identity_strict():
    s=text("scripts/validate_release_metadata.py")
    assert 'app/release.json' in s
    assert 'config.json' in s
    assert "RELEASE METADATA VALIDATION FAILED" in s

def test_v70_runtime_json_not_part_of_release_commit_contract():
    s=text("scripts/validate_release_metadata.py")
    assert 'DOCS.glob("*.json")' in s
    assert "validate_publish owns JSON parse/schema failures" in s
