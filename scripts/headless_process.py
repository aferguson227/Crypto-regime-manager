from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)
CREATE_NEW_PROCESS_GROUP=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
SW_HIDE=getattr(subprocess,"SW_HIDE",0)
STARTF_USESHOWWINDOW=getattr(subprocess,"STARTF_USESHOWWINDOW",0)

def startupinfo():
    if os.name!="nt":
        return None
    si=subprocess.STARTUPINFO()
    si.dwFlags |= STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    return si

def popen(command, *, cwd=None, stdout=None, stderr=None, env=None):
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.DEVNULL,
        env=env,
        creationflags=CREATE_NO_WINDOW,
        startupinfo=startupinfo(),
    )

def run(command, *, cwd=None, capture_output=False, text=False, env=None, check=False):
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        env=env,
        check=check,
        creationflags=CREATE_NO_WINDOW,
        startupinfo=startupinfo(),
    )

def pythonw_executable():
    exe=Path(sys.executable)
    if os.name=="nt":
        candidate=exe.with_name("pythonw.exe")
        if candidate.exists():
            return str(candidate)
    return str(exe)
