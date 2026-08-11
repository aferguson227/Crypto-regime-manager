from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v27_failure_bundle_feature_remains_present():
    assert (ROOT/"scripts"/"installer_failure_bundle.py").exists()
