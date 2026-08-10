from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')
def test_canonical_line_endings_policy_exists():
 s=text('.gitattributes')
 assert '* text=auto eol=lf' in s
 assert '*.zip binary' in s
def test_future_installer_has_semantic_source_classifier():
 s=text('scripts/installer_preflight.py')
 assert 'def semantic_source_changes' in s
 assert '--ignore-space-at-eol' in s
 assert "code=='??'" in s
def test_semantic_classifier_protects_staged_changes():
 s=text('scripts/installer_preflight.py')
 assert "'diff','--cached','--quiet','--ignore-space-at-eol'" in s
def test_semantic_classifier_keeps_runtime_separation():
 s=text('scripts/installer_preflight.py')
 assert 'is_runtime_or_publication(rel)' in s
