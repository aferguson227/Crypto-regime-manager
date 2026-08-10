from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')

def test_future_preflight_uses_git_native_source_filter():
 s=text('scripts/installer_preflight.py')
 assert "def git_source_status" in s
 assert ":(exclude,glob)docs/**/*.json" in s

def test_publication_json_cleanup_is_best_effort():
 s=text('scripts/installer_preflight.py')
 assert "def clean_publication_json_git_native" in s
 assert ":(glob)docs/**/*.json" in s
