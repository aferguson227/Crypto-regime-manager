#!/usr/bin/env python3
"""Canonical release validation coordinator.

Release metadata validation depends on the runtime diagnostics snapshot carrying
the current application version. Refresh it here so installers, builds and
manual release validation all use one authoritative sequence.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(module: str, *args: str) -> int:
    return subprocess.run([sys.executable, '-m', module, *args], cwd=ROOT).returncode


def validate() -> int:
    rc = run('scripts.validate_publish')
    if rc:
        return rc

    # Permanent ordering guard: regenerate runtime diagnostics before metadata
    # validation. This prevents stale diagnostics_runtime.json version drift.
    rc = run('scripts.diagnostics_manager', '--full')
    if rc:
        return rc

    rc = run('scripts.validate_release_metadata')
    if rc:
        return rc

    print('Unified release validation passed.')
    return 0


def main() -> int:
    argparse.ArgumentParser().parse_args()
    return validate()


if __name__ == '__main__':
    raise SystemExit(main())
