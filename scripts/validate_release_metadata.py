#!/usr/bin/env python3
"""Validate CRM software release identity separately from mutable runtime metadata.

V70 architecture:
- Software release identity is strict and must match VERSION.
- Runtime/publication snapshots may legitimately have been produced by an older
  CRM version during an upgrade window.
- Older runtime producer versions are reported as refresh-required, not as a
  software release failure.
- A runtime snapshot claiming a future application version is contradictory and
  remains fatal.
- JSON parse/shape validation remains the responsibility of validate_publish.

This removes runtime freshness from the software release gate without hiding it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

STRICT_RELEASE_JSON = {
    "version.json",
}

# Files that are clearly build/release artefacts rather than mutable live state.
# If additional strict artefacts are introduced, add them here rather than
# returning to "every docs JSON must equal VERSION".
OPTIONAL_STRICT_JSON = {
    "diagnostics.json",
}

def parse_version(value):
    try:
        return tuple(int(x) for x in str(value).split("."))
    except Exception:
        return None

def object_version(obj):
    if not isinstance(obj, dict):
        return None
    return (
        obj.get("application_version")
        or obj.get("version")
        or (obj.get("metadata") or {}).get("application_version")
    )

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main():
    errors = []
    warnings = []

    version_path = ROOT / "VERSION"
    release_path = ROOT / "app" / "release.json"
    if not version_path.exists():
        errors.append("VERSION is missing")
        expected = None
    else:
        expected = version_path.read_text(encoding="utf-8-sig").strip()

    if not release_path.exists():
        errors.append("app/release.json is missing")
    else:
        try:
            release = load_json(release_path)
            reported = str(release.get("version") or "")
            if expected and reported != expected:
                errors.append(f"app/release.json version={reported!r}, expected {expected!r}")
        except Exception as exc:
            errors.append(f"app/release.json cannot be parsed: {type(exc).__name__}: {exc}")

    # Core configuration is part of the software release identity when it
    # declares an application version.
    config_path = ROOT / "config.json"
    if config_path.exists() and expected:
        try:
            cfg = load_json(config_path)
            reported = None
            if isinstance(cfg, dict):
                reported = (cfg.get("app") or {}).get("version") or cfg.get("version")
            if reported and str(reported) != expected:
                errors.append(f"config.json application version={reported!r}, expected {expected!r}")
        except Exception as exc:
            errors.append(f"config.json cannot be parsed: {type(exc).__name__}: {exc}")

    # Strict release-owned docs metadata.
    if expected:
        for name in sorted(STRICT_RELEASE_JSON | OPTIONAL_STRICT_JSON):
            path = DOCS / name
            if not path.exists():
                if name in STRICT_RELEASE_JSON:
                    errors.append(f"docs/{name} is missing")
                continue
            try:
                obj = load_json(path)
                reported = object_version(obj)
                if reported and str(reported) != expected:
                    errors.append(f"docs/{name} application_version={reported!r}, expected {expected!r}")
            except Exception as exc:
                errors.append(f"docs/{name} cannot be parsed: {type(exc).__name__}: {exc}")

    # Every other docs JSON is mutable runtime/publication state for release
    # identity purposes. Older producer versions are allowed but visible.
    expected_tuple = parse_version(expected) if expected else None
    if DOCS.exists() and expected:
        for path in sorted(DOCS.glob("*.json")):
            if path.name in STRICT_RELEASE_JSON or path.name in OPTIONAL_STRICT_JSON:
                continue
            try:
                obj = load_json(path)
            except Exception:
                # validate_publish owns JSON parse/schema failures.
                continue
            reported = object_version(obj)
            if not reported or str(reported) == expected:
                continue
            actual_tuple = parse_version(reported)
            if expected_tuple and actual_tuple and actual_tuple > expected_tuple:
                errors.append(
                    f"docs/{path.name} claims future runtime application_version={reported!r}, "
                    f"installed application is {expected!r}"
                )
            else:
                warnings.append(
                    f"docs/{path.name} runtime producer={reported!r}; "
                    f"installed application={expected!r} — refresh required, not a release failure"
                )

    if warnings:
        print("RUNTIME METADATA REFRESH REQUIRED")
        for row in warnings:
            print(" - " + row)

    if errors:
        print("RELEASE METADATA VALIDATION FAILED")
        for row in errors:
            print(" - " + row)
        return 1

    print(
        f"Release metadata valid for V{expected}. "
        f"{len(warnings)} older runtime snapshot(s) may refresh asynchronously."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
