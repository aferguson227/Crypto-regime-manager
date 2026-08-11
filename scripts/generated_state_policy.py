from __future__ import annotations
import json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# Source assets under docs that must remain visible to Git.
SOURCE_DOCS_JSON={
    "docs/version.json",
}

# Runtime products that can be created before Git has ever tracked them.
KNOWN_UNTRACKED_RUNTIME={
    "docs/managed_bot_registry.json",
    "docs/portfolio_decision_consistency.json",
    "docs/regime_backtest_intelligence.json",
    "docs/resolution_state_status.json",
    "docs/runtime_reliability.json",
    "docs/runtime_reliability_card.json",
}

def _git(*args, check=True):
    return subprocess.run(
        ["git",*args],cwd=ROOT,capture_output=True,text=True,errors="replace",check=check
    )

def tracked_runtime_json():
    p=_git("ls-files","docs/*.json",check=False)
    return sorted(
        x.strip().replace("\\","/")
        for x in p.stdout.splitlines()
        if x.strip() and x.strip().replace("\\","/") not in SOURCE_DOCS_JSON
    )

def ensure_local_excludes():
    info=ROOT/".git"/"info"
    if not info.exists():
        return 0
    exclude=info/"exclude"
    existing=exclude.read_text(encoding="utf-8",errors="replace") if exclude.exists() else ""
    start="# CRM GENERATED STATE BEGIN"
    end="# CRM GENERATED STATE END"
    if start in existing and end in existing:
        before=existing.split(start,1)[0].rstrip()
        after=existing.split(end,1)[1].lstrip()
        existing=(before+"\n"+after).strip()+"\n" if (before or after) else ""
    block=[start,*sorted(KNOWN_UNTRACKED_RUNTIME),end]
    text=(existing.rstrip()+"\n" if existing.strip() else "")+"\n".join(block)+"\n"
    exclude.write_text(text,encoding="utf-8")
    return len(KNOWN_UNTRACKED_RUNTIME)

def apply():
    runtime=tracked_runtime_json()
    # Clear stale flags globally for docs JSON, then apply exactly the policy.
    tracked=_git("ls-files","docs/*.json",check=False).stdout.splitlines()
    tracked=[x.strip().replace("\\","/") for x in tracked if x.strip()]
    for i in range(0,len(tracked),40):
        _git("update-index","--no-skip-worktree","--",*tracked[i:i+40],check=False)
    for i in range(0,len(runtime),40):
        _git("update-index","--skip-worktree","--",*runtime[i:i+40],check=False)
    ignored=ensure_local_excludes()
    return {"tracked_runtime":len(runtime),"ignored_untracked":ignored}

def clear_for_upgrade(paths):
    tracked=[]
    for rel in paths:
        rel=str(rel).replace("\\","/")
        if _git("ls-files","--error-unmatch","--",rel,check=False).returncode==0:
            tracked.append(rel)
    for i in range(0,len(tracked),40):
        _git("update-index","--no-skip-worktree","--",*tracked[i:i+40],check=False)
    return len(tracked)

if __name__=="__main__":
    print(json.dumps(apply(),indent=2))
