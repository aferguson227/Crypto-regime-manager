from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_release_runtime_version_policy_exists():
    p=json.loads((ROOT/'config'/'publication_version_policy.json').read_text(encoding='utf-8'))
    assert 'version.json' in p['release_owned']
    assert 'system_integrity.json' in p['runtime_snapshots']
    assert p['rules']['runtime_snapshot_version_mismatch']=='REPORT_REFRESH_REQUIRED_BUT_DO_NOT_FAIL_SOURCE_RELEASE'

def test_publish_validator_separates_release_and_runtime_versions():
    t=(ROOT/'scripts'/'validate_publish.py').read_text(encoding='utf-8')
    assert 'publication_version_policy.json' in t
    assert 'runtime_version_warnings' in t
    assert 'RUNTIME PUBLICATION REFRESH REQUIRED' in t

def test_runtime_publication_checker_is_advisory_for_older_snapshots():
    t=(ROOT/'scripts'/'runtime_publication_version_check.py').read_text(encoding='utf-8')
    assert 'REFRESH REQUIRED' in t
    assert 'INVALID FUTURE SNAPSHOT' in t
