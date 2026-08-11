#!/usr/bin/env python3
"""Repair and verify the runtime_state_manager CLI parser.

The V69/V70 live-service crash loop was caused by calling parse_args() on the
_SubParsersAction returned by add_subparsers(), rather than on the root
ArgumentParser. This repair is deterministic, candidate-safe and idempotent.
"""
from __future__ import annotations
import argparse,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"scripts"/"runtime_state_manager.py"

def repair_text(text:str):
    # Detect the root ArgumentParser variable.
    roots=re.findall(r'(?m)^\s*(\w+)\s*=\s*argparse\.ArgumentParser\s*\(',text)
    root=roots[0] if roots else None
    if not root:
        raise RuntimeError("Could not identify root argparse.ArgumentParser in runtime_state_manager.py")

    # The known defect is sub.parse_args(); repair any SubParsersAction variable
    # that was created from the detected root parser.
    subvars=re.findall(r'(?m)^\s*(\w+)\s*=\s*'+re.escape(root)+r'\.add_subparsers\s*\(',text)
    repaired=text
    changed=False
    for sub in subvars:
        bad=f"{sub}.parse_args()"
        if bad in repaired:
            repaired=repaired.replace(bad,f"{root}.parse_args()")
            changed=True

    # Also handle the exact historical variable name defensively.
    if "sub.parse_args()" in repaired and root!="sub":
        repaired=repaired.replace("sub.parse_args()",f"{root}.parse_args()")
        changed=True

    return repaired,changed,root,subvars

def verify(text:str):
    if re.search(r'\bsub\.parse_args\(\)',text):
        return False,"subparser parse_args defect remains"
    roots=re.findall(r'(?m)^\s*(\w+)\s*=\s*argparse\.ArgumentParser\s*\(',text)
    if not roots:
        return False,"root ArgumentParser missing"
    root=roots[0]
    if f"{root}.parse_args()" not in text:
        return False,f"root parser {root}.parse_args() not found"
    return True,"PASS"

def main():
    if not TARGET.exists():
        print(f"RUNTIME STATE MANAGER REPAIR FAILED: missing {TARGET}")
        return 1
    original=TARGET.read_text(encoding="utf-8")
    repaired,changed,root,subs=repair_text(original)
    ok,detail=verify(repaired)
    if not ok:
        print("RUNTIME STATE MANAGER REPAIR FAILED:",detail)
        return 1
    if changed:
        TARGET.write_text(repaired,encoding="utf-8",newline="\n")
        print(f"Runtime state manager CLI repaired: root={root} subparsers={subs}")
    else:
        print(f"Runtime state manager CLI already correct: root={root}")
    print("Runtime state manager parser verification: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
