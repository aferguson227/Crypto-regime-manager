#!/usr/bin/env python3
"""CRM V70 Resident Runtime Service.

Single hidden supervisor for fast live trading truth, research and slow publication.

Safety boundaries:
- Does not place, cancel or modify exchange orders.
- Does not change CRM execution locks.
- Live truth remains owned by the existing KuCoin live-data service.
- Git/publication is deliberately low-priority and isolated from the fast data path.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path(os.getenv("CRM_DATA_ROOT", r"C:\Crypto\CRM_Data")) / "Runtime" / "State"
LOG_ROOT = Path(os.getenv("CRM_DATA_ROOT", r"C:\Crypto\CRM_Data")) / "Runtime" / "Logs"
CONTROL_ROOT = Path(os.getenv("CRM_DATA_ROOT", r"C:\Crypto\CRM_Data")) / "Runtime" / "Control"
STATUS = STATE_ROOT / "crm_resident_status.json"
LOCK = CONTROL_ROOT / "crm_resident.lock"
MAINT = CONTROL_ROOT / "maintenance.request"
STOP = CONTROL_ROOT / "stop.request"

HEARTBEAT_SECONDS = 2
LIVE_STALE_SECONDS = 75
PUBLICATION_SECONDS = int(os.getenv("CRM_PUBLICATION_SECONDS", "900"))
CANDIDATE_MODE = os.getenv("CRM_RESIDENT_CANDIDATE", "0") == "1"
RESEARCH_RESTART_SECONDS = 10
LIVE_RESTART_SECONDS = 5

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

def now():
    return datetime.now(timezone.utc).isoformat()

def atomic_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None

def process_alive(pid: int):
    if not pid:
        return False
    if os.name == "nt":
        r = subprocess.run(
            ["tasklist.exe", "/FI", f"PID eq {pid}", "/NH"],
            text=True, capture_output=True, creationflags=CREATE_NO_WINDOW
        )
        return str(pid) in (r.stdout or "")
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def ensure_single_instance():
    CONTROL_ROOT.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            old = int(LOCK.read_text(encoding="utf-8").strip())
        except Exception:
            old = 0
        if old and old != os.getpid() and process_alive(old):
            print(f"CRM resident already running pid={old}")
            return False
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    return True

def ps_command(script_name: str):
    script = ROOT / script_name
    return [
        "powershell.exe", "-NoProfile", "-NonInteractive",
        "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
        "-File", str(script)
    ]

def open_log(name):
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    return open(LOG_ROOT/name, "a", encoding="utf-8", buffering=1)

class Child:
    def __init__(self, name, command, restart_seconds=5):
        self.name=name
        self.command=command
        self.restart_seconds=restart_seconds
        self.proc=None
        self.last_start=0.0
        self.restarts=0
        self.log=None
        self.failure_times=[]
        self.circuit_open=False

    @property
    def pid(self):
        return self.proc.pid if self.proc and self.proc.poll() is None else None

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        # V19: deterministic crash-loop circuit breaker. Three exits within
        # 60 seconds stop automatic relaunch until the resident itself restarts.
        if self.proc and self.proc.poll() is not None:
            now=time.time()
            self.failure_times=[x for x in self.failure_times if now-x < 60]
            self.failure_times.append(now)
            if len(self.failure_times)>=3:
                self.circuit_open=True
        if self.circuit_open:
            return
        if time.time()-self.last_start < self.restart_seconds:
            return
        self.last_start=time.time()
        if self.log is None:
            self.log=open_log(f"{self.name}.log")
        self.proc=subprocess.Popen(
            self.command, cwd=ROOT, stdout=self.log, stderr=self.log,
            stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW
        )
        self.restarts += 1

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            self.proc=None
            return
        pid=self.proc.pid
        if os.name=="nt":
            subprocess.run(["taskkill.exe","/PID",str(pid),"/T","/F"],
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                           creationflags=CREATE_NO_WINDOW)
        else:
            self.proc.terminate()
        try:self.proc.wait(timeout=8)
        except Exception:pass
        self.proc=None

    def health(self):
        return {
            "name":self.name,
            "pid":self.pid,
            "running":bool(self.pid),
            "restart_count":max(0,self.restarts-1),
            "last_start_epoch":self.last_start or None,
            "circuit_open":self.circuit_open,
            "recent_failures":len(self.failure_times),
        }

class OneShot:
    def __init__(self, name, command):
        self.name=name
        self.command=command
        self.proc=None
        self.last_run=0.0
        self.last_exit=None
        self.log=None

    def run_if_due(self, seconds):
        if self.proc:
            rc=self.proc.poll()
            if rc is None:return
            self.last_exit=rc
            self.proc=None
        if time.time()-self.last_run < seconds:return
        self.last_run=time.time()
        if self.log is None:self.log=open_log(f"{self.name}.log")
        self.proc=subprocess.Popen(
            self.command,cwd=ROOT,stdout=self.log,stderr=self.log,
            stdin=subprocess.DEVNULL,creationflags=CREATE_NO_WINDOW
        )

    def stop(self):
        if self.proc and self.proc.poll() is None:
            if os.name=="nt":
                subprocess.run(["taskkill.exe","/PID",str(self.proc.pid),"/T","/F"],
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                               creationflags=CREATE_NO_WINDOW)
            else:self.proc.terminate()
        self.proc=None

    def health(self):
        return {
            "name":self.name,
            "running":bool(self.proc and self.proc.poll() is None),
            "pid":self.proc.pid if self.proc and self.proc.poll() is None else None,
            "last_run_epoch":self.last_run or None,
            "last_exit":self.last_exit,
        }

def live_heartbeat_age():
    d=read_json(STATE_ROOT/"kucoin_live_service_status.json")
    ts=parse_time(d.get("heartbeat_at") or d.get("generated_at"))
    return None if ts is None else max(0.0,time.time()-ts)

def write_status(mode, live, research, publication, note=""):
    age=live_heartbeat_age()
    state={
        "schema_version":"1.0",
        "application_version":"70.0.0",
        "generated_at":now(),
        "heartbeat_at":now(),
        "status":mode,
        "mode":mode,
        "pid":os.getpid(),
        "silent_background":True,
        "candidate_mode":CANDIDATE_MODE,
        "live_truth_path":"external_runtime_state",
        "git_in_live_data_path":False,
        "publication_interval_seconds":PUBLICATION_SECONDS,
        "live_heartbeat_age_seconds":round(age,1) if age is not None else None,
        "live_target_seconds":10,
        "order_target_seconds":20,
        "balance_target_seconds":30,
        "paper_target_seconds":30,
        "note":note,
        "components":{
            "kucoin_live_service":live.health(),
            "research_worker":research.health(),
            "publication":publication.health(),
        }
    }
    atomic_json(STATUS,state)

def main():
    STATE_ROOT.mkdir(parents=True,exist_ok=True)
    LOG_ROOT.mkdir(parents=True,exist_ok=True)
    CONTROL_ROOT.mkdir(parents=True,exist_ok=True)
    STOP.unlink(missing_ok=True)
    if not ensure_single_instance():return 0

    live=Child("kucoin-live",ps_command("RUN_KUCOIN_LIVE_SERVICE.ps1"),LIVE_RESTART_SECONDS)
    research=Child("research-worker",ps_command("RUN_RESEARCH_WORKER.ps1"),RESEARCH_RESTART_SECONDS)
    publication=OneShot("publication",ps_command("RUN_LOCAL_AGENT.ps1"))
    truth_guard=OneShot("portfolio-truth",[sys.executable,"-m","scripts.portfolio_truth_guard"])
    health_guard=OneShot("health-normalizer",[sys.executable,"-m","scripts.runtime_health_normalizer"])

    try:
        while not STOP.exists():
            if MAINT.exists():
                live.stop();research.stop();publication.stop()
                write_status("MAINTENANCE",live,research,publication,
                             "Installation/maintenance lock active. Runtime state is preserved.")
                time.sleep(HEARTBEAT_SECONDS)
                continue

            live.start();research.start()
            if not CANDIDATE_MODE:
                publication.run_if_due(PUBLICATION_SECONDS)
            truth_guard.run_if_due(10)
            health_guard.run_if_due(15)

            age=live_heartbeat_age()
            # Process can be alive but wedged; stale live truth is what matters.
            if age is not None and age > LIVE_STALE_SECONDS:
                live.stop()
                write_status("RECOVERING",live,research,publication,
                             f"Live heartbeat stale ({age:.0f}s); resident watchdog restarted the KuCoin service.")
                time.sleep(2)
                live.start()
            else:
                write_status("LIVE",live,research,publication,
                             "Resident service owns background runtime; Git publication is decoupled from live truth.")
            time.sleep(HEARTBEAT_SECONDS)
    finally:
        write_status("STOPPING",live,research,publication)
        health_guard.stop();truth_guard.stop();publication.stop();research.stop();live.stop()
        try:LOCK.unlink()
        except Exception:pass
    return 0

if __name__=="__main__":
    raise SystemExit(main())
