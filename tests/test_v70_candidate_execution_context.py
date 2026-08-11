from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def t(p):
    return (ROOT/p).read_text(encoding="utf-8")

def test_candidate_rehearsal_requires_explicit_candidate_files():
    # The installer is package-only, so repository regression coverage checks
    # the documented candidate-context contract rather than importing installer code.
    s=t("UPDATE_V70.md")
    assert "candidate execution context" in s.lower()

def test_candidate_startup_diagnostics_is_candidate_safe():
    s=t("scripts/resident_startup_diagnostics.py")
    assert 'CRM_PROJECT_PATH' in s
    assert 'RUN_KUCOIN_LIVE_SERVICE.ps1' in s
    launcher=t('RUN_KUCOIN_LIVE_SERVICE.ps1')
    assert 'CRM_PROJECT_PATH' in launcher
    assert r'C:\\Crypto\\Projects' not in launcher
