from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_manager_refreshes_runtime_diagnostics_before_metadata_validation():
    text = (ROOT / 'scripts' / 'release_manager.py').read_text(encoding='utf-8')
    runtime = "run('scripts.diagnostics_manager', '--full')"
    metadata = "run('scripts.validate_release_metadata')"
    assert runtime in text
    assert metadata in text
    assert text.index(runtime) < text.index(metadata)


def test_release_manager_keeps_publication_validation_first():
    text = (ROOT / 'scripts' / 'release_manager.py').read_text(encoding='utf-8')
    publish = "run('scripts.validate_publish')"
    runtime = "run('scripts.diagnostics_manager', '--full')"
    assert publish in text
    assert text.index(publish) < text.index(runtime)
