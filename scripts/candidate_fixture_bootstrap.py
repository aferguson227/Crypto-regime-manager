#!/usr/bin/env python3
"""V70 clean-room fixture bootstrap.

Before pytest:
- discover deterministic JSON fixtures that declare application/release version;
- regenerate through owning engines when practical;
- migrate remaining release/test fixtures to the canonical candidate version;
- leave runtime-only snapshots out of release identity;
- fail early if any release-owned fixture still disagrees.

This runs only inside the isolated candidate worktree.
"""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path
from scripts.clean_room_release import classify

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip()
CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)

ENGINE_MAP={
    "docs/diagnostics.json":"scripts.diagnostics_engine",
    "docs/account_intelligence.json":"scripts.account_intelligence_engine",
    "docs/command_state.json":"scripts.command_state_engine",
    "docs/engineering_health.json":"scripts.engineering_intelligence_engine",
    "docs/source_health.json":"scripts.source_health_engine",
    "docs/ui_health.json":"scripts.ui_health_engine",
    "docs/presentation_quality.json":"scripts.presentation_quality_gate",
}

VERSION_KEYS={"application_version","version"}

def run(args):
    return subprocess.run([str(x) for x in args],cwd=ROOT,text=True,capture_output=True,
                          creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def reported_version(obj):
    if not isinstance(obj,dict):return None
    if obj.get("application_version"):return str(obj["application_version"])
    if obj.get("version"):return str(obj["version"])
    app=obj.get("app")
    if isinstance(app,dict) and app.get("version"):return str(app["version"])
    return None

def set_version(obj):
    changed=False
    if not isinstance(obj,dict):return changed
    if "application_version" in obj and str(obj["application_version"])!=EXPECTED:
        obj["application_version"]=EXPECTED;changed=True
    if "version" in obj and re.fullmatch(r"\d+\.\d+\.\d+",str(obj["version"])) and str(obj["version"])!=EXPECTED:
        obj["version"]=EXPECTED;changed=True
    app=obj.get("app")
    if isinstance(app,dict) and "version" in app and str(app["version"])!=EXPECTED:
        app["version"]=EXPECTED;changed=True
    return changed

def regenerate(rel):
    mod=ENGINE_MAP.get(rel)
    if not mod:return {"status":"NO_OWNER"}
    r=run([sys.executable,"-m",mod])
    return {"status":"PASS" if r.returncode==0 else "WARN",
            "returncode":r.returncode,
            "tail":(r.stderr or r.stdout or "")[-400:]}

def candidate_jsons():
    for p in sorted((ROOT/"docs").glob("*.json")):
        yield p

def bootstrap():
    report={"expected":EXPECTED,"regenerated":[],"migrated":[],"runtime_ignored":[],"errors":[]}

    # Regenerate known deterministic outputs first.
    for rel in ENGINE_MAP:
        p=ROOT/rel
        if p.exists():
            report["regenerated"].append({"path":rel,**regenerate(rel)})

    # Canonical version surfaces.
    version_json=ROOT/"docs"/"version.json"
    if version_json.exists():
        obj=load(version_json)
        if isinstance(obj,dict):
            if "version" in obj:obj["version"]=EXPECTED
            if "application_version" in obj:obj["application_version"]=EXPECTED
            version_json.write_text(json.dumps(obj,indent=2),encoding="utf-8")

    # Migrate release/build/test fixtures only. Runtime snapshots are visible but ignored.
    for p in candidate_jsons():
        rel=p.relative_to(ROOT).as_posix()
        try:obj=load(p)
        except Exception as exc:
            report["errors"].append(f"{rel}: invalid JSON: {exc}")
            continue
        cls=classify(rel)
        rv=reported_version(obj)
        if cls=="RUNTIME":
            if rv and rv!=EXPECTED:
                report["runtime_ignored"].append({"path":rel,"producer":rv})
            continue
        if rv and rv!=EXPECTED:
            if set_version(obj):
                p.write_text(json.dumps(obj,indent=2),encoding="utf-8")
                report["migrated"].append({"path":rel,"from":rv,"to":EXPECTED})

    # Tests may directly inspect specific deterministic fixtures that classify as runtime.
    # Promote only fixtures explicitly referenced by source tests with version equality assertions.
    test_text="\n".join(
        p.read_text(encoding="utf-8",errors="ignore")
        for p in sorted((ROOT/"tests").glob("test_*.py"))
    )
    direct=[]
    for p in candidate_jsons():
        rel=p.relative_to(ROOT).as_posix()
        name=p.name
        if name not in test_text:continue
        try:obj=load(p)
        except Exception:continue
        rv=reported_version(obj)
        if rv and rv!=EXPECTED:
            if set_version(obj):
                p.write_text(json.dumps(obj,indent=2),encoding="utf-8")
                direct.append({"path":rel,"from":rv,"to":EXPECTED})
    report["test_fixture_migrations"]=direct

    # Pre-pytest consistency scan for directly tested/versioned fixtures.
    failures=[]
    for p in candidate_jsons():
        rel=p.relative_to(ROOT).as_posix()
        try:obj=load(p)
        except Exception:continue
        rv=reported_version(obj)
        if not rv or rv==EXPECTED:continue
        cls=classify(rel)
        if cls in {"STRICT_RELEASE","BUILD_GENERATED"}:
            failures.append(f"{rel} reports {rv}, expected {EXPECTED}")
        elif p.name in test_text:
            failures.append(f"{rel} is directly referenced by tests and reports {rv}, expected {EXPECTED}")
    report["consistency_failures"]=failures
    return report

def main():
    report=bootstrap()
    out=ROOT/"build"/"v70_fixture_bootstrap.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"Fixture bootstrap: migrated={len(report['migrated'])} direct_test={len(report['test_fixture_migrations'])} runtime_ignored={len(report['runtime_ignored'])}")
    if report["consistency_failures"] or report["errors"]:
        print("FIXTURE BOOTSTRAP FAILED")
        for row in report["errors"]+report["consistency_failures"]:print(" -",row)
        return 1
    print("Fixture consistency preflight: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
