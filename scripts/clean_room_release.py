#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path

PROJECT=Path(os.getenv("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))
DATA_ROOT=Path(os.getenv("CRM_DATA_ROOT",r"C:\Crypto\CRM_Data"))
INSTALLER_ROOT=DATA_ROOT/"Installer"
CANDIDATE_ROOT=INSTALLER_ROOT/"Candidate"
MANIFEST=INSTALLER_ROOT/"clean_room_manifest.json"
CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)

STRICT_RELEASE_FILES={"VERSION","app/release.json","config.json","docs/version.json"}
BUILD_GENERATED_JSON={
 "docs/engineering_health.json","docs/engineering_schedule.json","docs/presentation_quality.json",
 "docs/repository_health.json","docs/source_health.json","docs/ui_health.json",
 "docs/visual_issues.json","docs/diagnostics.json"
}
RUNTIME_PREFIXES=("docs/kucoin_","docs/live_","docs/local_agent_","docs/managed_bot_","docs/paper_",
"docs/research_","docs/portfolio_","docs/execution_","docs/freshness_","docs/remediation_",
"docs/self_healing_","docs/deployment_","docs/recommendation_","docs/validation_","docs/issue_",
"docs/optimisation_","docs/candidate_","docs/coin_","docs/cross_exchange_","docs/continuation_",
"docs/independent_trade_","docs/native_execution_","docs/global_market")

def run(args,cwd=None,check=True):
 r=subprocess.run([str(x) for x in args],cwd=cwd or PROJECT,text=True,capture_output=True,
                  creationflags=CREATE_NO_WINDOW if os.name=="nt" else 0)
 if check and r.returncode:
  raise RuntimeError((r.stderr or r.stdout or "").strip())
 return r

def classify(rel):
 rel=rel.replace("\\","/")
 if rel in STRICT_RELEASE_FILES:return "STRICT_RELEASE"
 if rel in BUILD_GENERATED_JSON:return "BUILD_GENERATED"
 if rel.startswith(RUNTIME_PREFIXES) and rel.endswith(".json"):return "RUNTIME"
 if rel.startswith("docs/") and rel.endswith(".json"):return "RUNTIME"
 return "SOURCE"

def remove_candidate():
 run(["git","worktree","remove","--force",str(CANDIDATE_ROOT)],check=False)
 shutil.rmtree(CANDIDATE_ROOT,ignore_errors=True)

def create_candidate(ref="HEAD"):
 remove_candidate()
 CANDIDATE_ROOT.parent.mkdir(parents=True,exist_ok=True)
 r=run(["git","worktree","add","--detach",str(CANDIDATE_ROOT),ref],check=False)
 if r.returncode:raise RuntimeError("Could not create isolated candidate worktree.")
 return CANDIDATE_ROOT

def regenerate_build_outputs(candidate):
 mods=["scripts.engineering_intelligence_engine","scripts.presentation_quality_gate",
       "scripts.source_health_engine","scripts.ui_health_engine","scripts.autonomous_diagnostics"]
 out=[]
 for mod in mods:
  script=candidate/"scripts"/(mod.split(".")[-1]+".py")
  if not script.exists():
   out.append({"module":mod,"status":"SKIPPED"});continue
  r=run(["python","-m",mod],cwd=candidate,check=False)
  out.append({"module":mod,"status":"PASS" if r.returncode==0 else "WARN","returncode":r.returncode})
 return out

def write_manifest(candidate,extra=None):
 rows=[]
 for p in candidate.rglob("*"):
  if p.is_file():
   rel=p.relative_to(candidate).as_posix()
   rows.append({"path":rel,"class":classify(rel)})
 data={"schema_version":"1.0","candidate":str(candidate),
       "runtime_is_release_gate":False,"production_repo_validated_in_place":False,
       "build_outputs_regenerated_in_candidate":True,"files":rows}
 if extra:data.update(extra)
 MANIFEST.parent.mkdir(parents=True,exist_ok=True)
 MANIFEST.write_text(json.dumps(data,indent=2),encoding="utf-8")
 return data

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("action",choices=("create","remove","classify"))
 ap.add_argument("--ref",default="HEAD");ap.add_argument("--path")
 a=ap.parse_args()
 if a.action=="create":print(create_candidate(a.ref));return 0
 if a.action=="remove":remove_candidate();return 0
 print(classify(a.path or ""));return 0
if __name__=="__main__":raise SystemExit(main())
