from __future__ import annotations
import json, os, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

def _run(cmd,cwd=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=30)
        return {"command":cmd,"returncode":p.returncode,"stdout":p.stdout[-16000:],"stderr":p.stderr[-16000:]}
    except Exception as e:return {"command":cmd,"error":repr(e)}

def _tail(p,n=40000):
    p=Path(p)
    try:return p.read_text(encoding="utf-8",errors="replace")[-n:] if p.exists() else None
    except Exception as e:return "<unreadable %r>"%e

def collect(reason="installer failure"):
    reason=reason.replace("\x00","\\0")
    runtime=Path(os.environ.get("CRM_RUNTIME_ROOT",r"C:\Crypto\CRM_Data"))
    inst=runtime/"Installer"; inst.mkdir(parents=True,exist_ok=True)
    project=Path(os.environ.get("CRM_PROJECT_PATH",r"C:\Crypto\Projects"))
    candidate=inst/"Candidate"
    bundle=inst/("FAILED_INSTALL_"+datetime.now().strftime("%Y%m%d-%H%M%S"))
    bundle.mkdir(parents=True,exist_ok=True)
    report={
      "generated_at":datetime.now(timezone.utc).isoformat(),"reason":reason,
      "python":sys.executable,"python_version":sys.version,"platform":platform.platform(),
      "project":str(project),"candidate":str(candidate),
      "environment":{k:os.environ.get(k) for k in ("CRM_PROJECT_PATH","CRM_RUNTIME_ROOT","CRM_PYTHON","PYTHONPATH")},
      "git_status":_run(["git","status","--porcelain=v1"],project),
      "git_head":_run(["git","rev-parse","HEAD"],project),
      "git_origin_main":_run(["git","rev-parse","origin/main"],project),
      "git_recent":_run(["git","log","-8","--oneline","--decorate"],project),
      "artifacts":{}
    }
    for name in ("resident_startup_diagnostics.json","kucoin_first_heartbeat.json",
                 "candidate_acceptance.json","installer_doctor.json","resident_task_install_failure.json",
                 "kucoin_worker_first_boot.log","resident.log","kucoin_live_service.log"):
        for base in (inst,runtime/"Logs",runtime/"Runtime"/"Logs"):
            p=base/name
            if p.exists():report["artifacts"][str(p)]=_tail(p)
    if candidate.exists():
        report["candidate_pytest"]=_run([sys.executable,"-m","pytest","-q","tests","--tb=short"],candidate)
    (bundle/"failure_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    (bundle/"README.txt").write_text(
        "CRM failed-install diagnostic bundle\n\n"
        "Attach failure_report.json to the next repair request.\n"
        "The report includes Git state, candidate tests, environment and runtime diagnostics.\n",
        encoding="utf-8")
    (inst/"LATEST_FAILED_INSTALL.txt").write_text(str(bundle),encoding="utf-8")
    print("Failure diagnostic bundle:",bundle)
    return bundle

if __name__=="__main__":
    collect(" ".join(sys.argv[1:]) or "manual collection")
