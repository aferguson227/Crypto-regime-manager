from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_manager_synchronises_identity_before_validation():
    text = (ROOT/'scripts/release_manager.py').read_text(encoding='utf-8')
    sync = "run('scripts.release_identity_sync')"
    publish = "run('scripts.validate_publish')"
    assert sync in text and publish in text
    assert text.index(sync) < text.index(publish)


def test_identity_sync_is_metadata_only():
    text = (ROOT/'scripts/release_identity_sync.py').read_text(encoding='utf-8')
    assert "application_version" in text
    assert "release_name" in text
    assert "threecommas" not in text.lower()
    assert "capital" not in text.lower()
