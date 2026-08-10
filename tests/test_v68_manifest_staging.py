from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_manifest_helper_exists():
 t=(ROOT/"scripts/installer_preflight.py").read_text(encoding="utf-8")
 assert "def build_release_stage_manifest" in t
 assert "allowed={'.html','.js','.css','.md','.txt'}" in t
def test_manifest_does_not_include_docs_json():
 t=(ROOT/"scripts/installer_preflight.py").read_text(encoding="utf-8")
 segment=t[t.index("def build_release_stage_manifest"):]
 assert "'.json'" not in segment[segment.index("allowed={"):segment.index("files.extend",segment.index("allowed={"))]
