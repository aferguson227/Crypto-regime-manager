#!/usr/bin/env python3
"""Cloud automation watchdog with independent application and 3Commas health."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.release import application_version

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "cloud_reliability.json"


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def parse_dt(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def age_hours(value: Any) -> float | None:
    observed = parse_dt(value)
    if observed is None:
        return None
    return round((datetime.now(timezone.utc) - observed).total_seconds() / 3600, 2)


def classify_age(stamp: Any, warning: float, failure: float) -> str:
    age = age_hours(stamp)
    if age is None:
        return "unknown"
    if age > failure:
        return "failure"
    if age > warning:
        return "warning"
    return "healthy"


def endpoint_summary(value: Any) -> dict[str, Any]:
    endpoints = value if isinstance(value, dict) else {}
    failures = []
    for name, row in endpoints.items():
        if not isinstance(row, dict):
            continue
        if row.get("status") != "pass":
            failures.append(
                {
                    "endpoint": name,
                    "category": row.get("category") or "unknown",
                    "message": row.get("message"),
                    "http_status": row.get("http_status"),
                }
            )
    return {
        "results": endpoints,
        "failure_count": len(failures),
        "failures": failures,
        "primary_failure_category": failures[0]["category"] if failures else None,
    }


def workflow_check(path: Path, expected_module: str, cron_hint: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    findings: list[str] = []
    if "workflow_dispatch:" not in text:
        findings.append("Manual recovery trigger is missing.")
    if "schedule:" not in text or "cron:" not in text:
        findings.append("Scheduled trigger is missing.")
    if expected_module not in text:
        findings.append(f"Module execution is missing: {expected_module}")
    if "permissions:" not in text or "contents: write" not in text:
        findings.append("Explicit contents write permission is missing.")
    if cron_hint not in text:
        findings.append(f"Expected cron not found: {cron_hint}")
    direct = re.findall(r"run:\s*python\s+(scripts/[^\s]+\.py)", text)
    if direct:
        findings.append("Direct script execution may break package imports: " + ", ".join(direct))
    return {
        "file": str(path.relative_to(ROOT)),
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "module_execution": expected_module,
        "expected_cron": cron_hint,
    }


def threecommas_pipeline(three: dict[str, Any]) -> dict[str, Any]:
    attempted = three.get("last_attempt_at") or three.get("generated_at")
    succeeded = three.get("last_success_at")
    status = str(three.get("status") or "unknown")
    attempt_state = classify_age(attempted, 1.5, 3)
    success_state = classify_age(succeeded, 2, 6)
    endpoint_info = endpoint_summary(three.get("endpoint_diagnostics"))

    if status == "error" or success_state == "failure":
        state = "failure"
    elif status == "partial" or attempt_state == "warning" or success_state == "warning":
        state = "warning"
    elif attempt_state == "healthy" and success_state == "healthy":
        state = "healthy"
    else:
        state = "unknown"

    return {
        "name": "3Commas read-only sync",
        "state": state,
        "last_attempt_at": attempted,
        "last_attempt_age_hours": age_hours(attempted),
        "last_success_at": succeeded,
        "last_success_age_hours": age_hours(succeeded),
        "expected_cadence_hours": 1,
        "warning_after_hours": 2,
        "failure_after_hours": 6,
        "source_status": status,
        "message": three.get("message"),
        "endpoint_diagnostics": endpoint_info,
    }


def application_pipeline(cloud: dict[str, Any]) -> dict[str, Any]:
    attempted = cloud.get("started_at") or cloud.get("generated_at") or cloud.get("completed_at")
    succeeded = cloud.get("completed_at") if str(cloud.get("state") or "").lower() not in {"error", "fail", "failure"} else None
    state = classify_age(succeeded, 6, 12)
    if str(cloud.get("state") or "").lower() in {"error", "fail", "failure"}:
        state = "failure"
    return {
        "name": "Main market/application refresh",
        "state": state,
        "last_attempt_at": attempted,
        "last_attempt_age_hours": age_hours(attempted),
        "last_success_at": succeeded,
        "last_success_age_hours": age_hours(succeeded),
        "expected_cadence_hours": 4,
        "warning_after_hours": 6,
        "failure_after_hours": 12,
        "source_status": cloud.get("state"),
        "message": cloud.get("message"),
    }


def build() -> dict[str, Any]:
    three = load(DOCS / "threecommas.json")
    cloud = load(DOCS / "cloud_status.json")
    pipelines = {
        "threecommas": threecommas_pipeline(three),
        "application": application_pipeline(cloud),
    }
    workflows = [
        workflow_check(
            ROOT / ".github/workflows/threecommas-update.yml",
            "python -m scripts.threecommas_sync",
            "37 * * * *",
        ),
        workflow_check(
            ROOT / ".github/workflows/multi-coin-update.yml",
            "python -m scripts.cloud_update",
            "18 0,4,8,12,16,20 * * *",
        ),
    ]
    states = [row["state"] for row in pipelines.values()]
    workflow_failure = any(row["status"] == "fail" for row in workflows)
    status = "FAILURE" if workflow_failure or "failure" in states else "WARNING" if "warning" in states or "unknown" in states else "HEALTHY"
    repo = os.getenv("GITHUB_REPOSITORY")
    run = os.getenv("GITHUB_RUN_ID")
    payload = {
        "schema_version": "2.0",
        "application_version": application_version(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": hashlib.sha256(
            json.dumps(
                {
                    "three_attempt": pipelines["threecommas"]["last_attempt_at"],
                    "three_success": pipelines["threecommas"]["last_success_at"],
                    "cloud_success": pipelines["application"]["last_success_at"],
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:20],
        "status": status,
        "pipelines": pipelines,
        "sources": list(pipelines.values()),
        "threecommas_endpoints": pipelines["threecommas"]["endpoint_diagnostics"]["results"],
        "workflows": workflows,
        "github": {
            "repository": repo,
            "workflow_run_id": run,
            "run_url": f"https://github.com/{repo}/actions/runs/{run}" if repo and run else None,
        },
        "automation_policy": {
            "routine_manual_runs_required": False,
            "manual_run_purpose": "Recovery and diagnosis only",
            "threecommas_cadence": "hourly at minute 37 UTC",
            "main_refresh_cadence": "every four hours at minute 18 UTC",
        },
        "read_only": True,
    }
    return payload


def main() -> int:
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Cloud reliability written: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
