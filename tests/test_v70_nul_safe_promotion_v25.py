from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v25_failure_bundle_sanitises_nul_in_reason():
    s=(ROOT/"scripts"/"installer_failure_bundle.py").read_text(encoding="utf-8")
    assert 'reason=reason.replace("\\x00","\\\\0")' in s
