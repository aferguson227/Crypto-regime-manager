from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def test_release_identity_is_v33_0_2():
    release = load("app/release.json")
    version = load("docs/version.json")
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "34.0.0"
    assert release["version"] == version["version"] == "34.0.0"
    assert release["release_name"] == version["release_name"]


def test_release_and_runtime_diagnostics_are_separate():
    source = (ROOT / "scripts/diagnostics_engine.py").read_text(encoding="utf-8")
    assert 'RELEASE_OUTPUT = DOCS / "diagnostics.json"' in source
    assert 'RUNTIME_OUTPUT = DOCS / "diagnostics_runtime.json"' in source
    assert "--release-snapshot" in source
    assert "docs/diagnostics_runtime.json" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_cloud_watchdog_has_independent_pipeline_freshness():
    cloud = load("docs/cloud_reliability.json")
    assert cloud["schema_version"] == "2.0"
    assert set(cloud["pipelines"]) == {"threecommas", "application"}
    three = cloud["pipelines"]["threecommas"]
    assert "last_attempt_at" in three and "last_success_at" in three
    assert three["expected_cadence_hours"] == 1
    assert "endpoint_diagnostics" in three


def test_threecommas_sync_preserves_last_success_and_read_only_boundary():
    source = (ROOT / "scripts/integrations/threecommas.py").read_text(encoding="utf-8")
    assert "load_previous_payload" in source
    assert '"last_attempt_at"' in source
    assert '"last_success_at"' in source
    assert "ALLOWED_PATHS" in source
    assert "read_only" in source
