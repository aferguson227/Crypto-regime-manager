from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")
def test_clean_room_uses_git_worktree():
 s=t("scripts/clean_room_release.py");assert '"worktree","add"' in s and "CANDIDATE_ROOT" in s
def test_runtime_json_not_release_gate():
 s=t("scripts/clean_room_release.py");assert 'return "RUNTIME"' in s and "runtime_is_release_gate" in s
def test_build_outputs_regenerated_in_candidate():
 s=t("scripts/clean_room_release.py");assert "regenerate_build_outputs" in s and "engineering_intelligence_engine" in s
def test_clean_room_validator_separates_runtime_versions():
 s=t("scripts/validate_clean_room_release.py");assert "RUNTIME SNAPSHOTS EXCLUDED FROM RELEASE GATE" in s
