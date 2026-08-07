#!/usr/bin/env python3
"""Canonical generated-output lifecycle manager.

Files declared in config/generated_outputs_policy.json are treated as disposable
runtime outputs. Tracked runtime outputs are restored to the committed snapshot;
untracked runtime outputs are removed. Source files are never touched unless they
are explicitly declared by policy.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'config/generated_outputs_policy.json'


def policy() -> dict:
    return json.loads(POLICY.read_text(encoding='utf-8-sig'))


def tracked(rel: str) -> bool:
    return subprocess.run(
        ['git', 'ls-files', '--error-unmatch', '--', rel],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def restore_tracked(rel: str) -> bool:
    if not tracked(rel):
        return False
    return subprocess.run(
        ['git', 'restore', '--worktree', '--', rel],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def remove_untracked_runtime(rel: str) -> bool:
    if tracked(rel):
        return False
    p = ROOT / rel
    if not p.exists():
        return False
    # Runtime-output policy is intentionally file-based; never recurse here.
    if not p.is_file():
        return False
    p.unlink()
    return True


def clean() -> dict:
    restored = []
    removed = []
    for rel in policy().get('runtime_generated_patterns') or []:
        if tracked(rel):
            if restore_tracked(rel):
                restored.append(rel)
        elif remove_untracked_runtime(rel):
            removed.append(rel)
    return {'restored': restored, 'removed': removed}


def status() -> dict:
    items = []
    for rel in policy().get('runtime_generated_patterns') or []:
        p = ROOT / rel
        items.append({'path': rel, 'exists': p.exists(), 'tracked': tracked(rel)})
    return {'runtime_outputs': items}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['clean', 'status'], nargs='?', default='clean')
    a = ap.parse_args()
    if a.action == 'status':
        print(json.dumps(status(), indent=2))
        return 0

    result = clean()
    print(
        'Generated-output cleanup complete: '
        f"{len(result['restored'])} tracked runtime files restored; "
        f"{len(result['removed'])} untracked runtime files removed safely."
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
