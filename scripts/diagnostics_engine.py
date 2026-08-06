#!/usr/bin/env python3
"""Crypto Regime Manager diagnostics and acceptance engine.

Produces a machine-readable health report and a redacted ZIP suitable for review.
It is observational only and never changes bots, orders, settings or funds.
"""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "diagnostics.json"
EXPORT_DIR = ROOT / "diagnostics_exports"
MOJIBAKE = ("â€™", "â€œ", "â€", "Â·", "â†", "ï¿½", "\ufffd")
SECRET_PATTERNS = (
    re.compile(r"BEGIN (?:RSA )?PRIVATE KEY", re.I),
    re.compile(r"THREECOMMAS_(?:API|RSA|SECRET|PRIVATE)", re.I),
    re.compile(r"bot[_ -]?control[^\s\"']*@", re.I),
    re.compile(r"(?:api[_-]?key|secret|private[_-]?key)\s*[=:]\s*[\"'][^\"']+", re.I),
)

@dataclass
class Check:
    id: str
    name: str
    category: str
    status: str
    message: str
    evidence: list[str]
    required: bool = True

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_release() -> Check:
    evidence=[]
    try:
        release=read_json(ROOT/'app'/'release.json')
        version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
        doc=read_json(DOCS/'version.json')
        config=read_json(ROOT/'config.json')
        values=[version,release.get('version'),doc.get('version'),config.get('version')]
        evidence=[f"VERSION={values[0]}",f"release={values[1]}",f"docs={values[2]}",f"config={values[3]}"]
        ok=len(set(values))==1 and values[0]==str(release.get('version'))
        return Check('release.identity','Release identity','release','pass' if ok else 'fail','All release sources agree.' if ok else 'Release version sources disagree.',evidence)
    except Exception as exc:
        return Check('release.identity','Release identity','release','fail',str(exc),evidence)


def check_routes() -> Check:
    missing=[]; evidence=[]
    try:
        routes=read_json(ROOT/'config'/'routes.json')['routes']
        for route in routes:
            path=DOCS/route['path']
            evidence.append(route['path'])
            if not path.exists(): missing.append(route['path'])
        return Check('ui.routes','Route manifest','interface','fail' if missing else 'pass',f"Missing routes: {', '.join(missing)}" if missing else f"{len(routes)} declared routes exist.",evidence)
    except Exception as exc:
        return Check('ui.routes','Route manifest','interface','fail',str(exc),evidence)


def html_checks() -> list[Check]:
    broken=[]; mojibake=[]; duplicate_ids=[]; missing_meta=[]; evidence=[]
    for page in sorted(DOCS.glob('*.html')):
        text=page.read_text(encoding='utf-8',errors='replace')
        evidence.append(page.name)
        low=text.lower()
        if '<meta charset="utf-8"' not in low and "<meta charset='utf-8'" not in low: missing_meta.append(page.name)
        if any(token in text for token in MOJIBAKE): mojibake.append(page.name)
        ids=re.findall(r'\bid=["\']([^"\']+)',text,re.I)
        dup=sorted({x for x in ids if ids.count(x)>1})
        if dup: duplicate_ids.append(f"{page.name}: {', '.join(dup)}")
        for ref in re.findall(r'(?:href|src)=["\']([^"\']+)',text,re.I):
            ref=ref.split('?')[0].split('#')[0]
            if not ref or ref.startswith(('http:','https:','mailto:','javascript:','data:')): continue
            parsed=urlparse(ref)
            if parsed.path.endswith(('.html','.css','.js','.json')) and not (page.parent/parsed.path).exists():
                broken.append(f"{page.name} -> {parsed.path}")
    return [
        Check('ui.assets','HTML asset references','interface','fail' if broken else 'pass',f"{len(broken)} missing local references." if broken else f"All references across {len(evidence)} HTML pages resolve.",broken[:30] or evidence),
        Check('ui.encoding','UTF-8 presentation','interface','fail' if mojibake or missing_meta else 'pass',f"Encoding problems in {len(set(mojibake+missing_meta))} pages." if mojibake or missing_meta else 'No known mojibake and every page declares UTF-8.',sorted(set(mojibake+missing_meta))),
        Check('ui.ids','Duplicate DOM identifiers','interface','warn' if duplicate_ids else 'pass',f"Duplicate IDs found on {len(duplicate_ids)} pages." if duplicate_ids else 'No duplicate HTML IDs detected.',duplicate_ids,required=False),
    ]


def json_checks() -> list[Check]:
    invalid=[]; stale=[]; evidence=[]
    now=datetime.now(timezone.utc)
    for path in sorted(DOCS.glob('*.json')):
        try:
            obj=read_json(path); evidence.append(path.name)
            stamp=None
            if isinstance(obj,dict):
                stamp=obj.get('generated_at') or obj.get('observed_at') or (obj.get('metadata') or {}).get('generated_at')
            if stamp:
                try:
                    dt=datetime.fromisoformat(str(stamp).replace('Z','+00:00'))
                    age=(now-dt.astimezone(timezone.utc)).total_seconds()/3600
                    if age>168: stale.append(f"{path.name}: {age:.0f}h")
                except Exception: pass
        except Exception as exc: invalid.append(f"{path.name}: {exc}")
    return [
        Check('data.json','Published JSON validity','data','fail' if invalid else 'pass',f"{len(invalid)} invalid JSON files." if invalid else f"{len(evidence)} JSON files parse successfully.",invalid or evidence),
        Check('data.freshness','Published data freshness','data','warn' if stale else 'pass',f"{len(stale)} timestamped files are older than seven days." if stale else 'No timestamped output is older than seven days.',stale,required=False),
    ]


def readonly_check() -> Check:
    evidence=[]; findings=[]
    paths=list((ROOT/'scripts'/'integrations').glob('*.py'))+[ROOT/'scripts'/'threecommas_sync.py']
    for path in paths:
        if not path.exists(): continue
        text=path.read_text(encoding='utf-8',errors='ignore'); evidence.append(str(path.relative_to(ROOT)))
        if re.search(r'\b(?:POST|PUT|PATCH|DELETE)\b',text,re.I): findings.append(f"{path.name}: mutation verb present")
        if re.search(r'/(?:bots|deals|accounts)/[^\s\"\']+/(?:enable|disable|start|stop|update|panic_sell|cancel)',text,re.I): findings.append(f"{path.name}: mutation endpoint present")
    return Check('safety.read_only','3Commas read-only boundary','safety','fail' if findings else 'pass','Potential mutation capability detected.' if findings else 'No write verbs or known mutation endpoints detected.',findings or evidence)


def secret_check() -> Check:
    findings=[]
    for path in list(DOCS.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.json','.html','.js','.css','.txt','.csv'}: continue
        text=path.read_text(encoding='utf-8',errors='ignore')
        if any(p.search(text) for p in SECRET_PATTERNS): findings.append(str(path.relative_to(ROOT)))
    return Check('safety.secrets','Published secret scan','safety','fail' if findings else 'pass',f"Secret-like material detected in {len(findings)} files." if findings else 'No private keys, API secrets or bot-control tokens detected in published files.',findings)


def workflow_automation_check() -> Check:
    findings=[]; evidence=[]
    expectations=[('.github/workflows/threecommas-update.yml','python -m scripts.threecommas_sync','37 * * * *'),('.github/workflows/multi-coin-update.yml','python -m scripts.cloud_update','18 0,4,8,12,16,20 * * *')]
    for rel,module,cron in expectations:
        path=ROOT/rel; evidence.append(rel)
        if not path.exists(): findings.append(f'{rel}: missing'); continue
        text=path.read_text(encoding='utf-8')
        if module not in text: findings.append(f'{rel}: missing module execution {module}')
        if cron not in text: findings.append(f'{rel}: missing expected cron {cron}')
        if 'workflow_dispatch:' not in text: findings.append(f'{rel}: missing manual recovery trigger')
        if re.search(r'run:\s*python\s+scripts/[^\s]+\.py',text): findings.append(f'{rel}: direct script execution may break package imports')
    return Check('cloud.workflows','GitHub workflow automation','cloud','fail' if findings else 'pass','Workflow automation configuration is valid.' if not findings else 'Workflow automation problems detected.',findings or evidence)

def source_checks() -> list[Check]:
    required=['strategies.json','threecommas.json','configuration_reconciliation.json','operating_state.json','capital_intelligence.json','deployment_intelligence.json','recommendation_intelligence.json','outcome_intelligence.json','portfolio_intelligence.json','cloud_reliability.json','command_state.json','system_integrity.json','cloud_status.json']
    missing=[x for x in required if not (DOCS/x).exists()]
    src=[]
    for name in required:
        path=DOCS/name
        if path.exists(): src.append(f"{name} ({path.stat().st_size} bytes)")
    return [Check('sources.required','Required operating sources','sources','fail' if missing else 'pass',f"Missing: {', '.join(missing)}" if missing else 'All required operating sources are present.',missing or src)]


def run_command_check(identifier:str,name:str,args:list[str]) -> Check:
    try:
        proc=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=180)
        tail=(proc.stdout+'\n'+proc.stderr).strip().splitlines()[-12:]
        return Check(identifier,name,'acceptance','pass' if proc.returncode==0 else 'fail',f"Exited with code {proc.returncode}.",tail)
    except Exception as exc:
        return Check(identifier,name,'acceptance','fail',str(exc),[])


def find_edge() -> Path|None:
    candidates=[]
    for env in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
        base=os.getenv(env)
        if base:
            candidates += [Path(base)/'Microsoft/Edge/Application/msedge.exe',Path(base)/'Microsoft/Edge Beta/Application/msedge.exe']
    return next((p for p in candidates if p.exists()),None)


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        # Browser capture requests are expected and should not be emitted to
        # stderr, where Windows PowerShell 5.1 may treat them as build errors.
        return


def capture_screenshots(routes:Iterable[str],dest:Path) -> tuple[list[str],list[str]]:
    edge=find_edge()
    if not edge: return [],['Microsoft Edge was not found; browser screenshots skipped.']
    dest.mkdir(parents=True,exist_ok=True)
    handler=lambda *a,**kw:QuietHTTPRequestHandler(*a,directory=str(DOCS),**kw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    made=[]; errors=[]
    try:
        port=server.server_address[1]
        for route in routes:
            out=dest/(Path(route).stem+'.png')
            cmd=[str(edge),'--headless=new','--disable-gpu','--hide-scrollbars','--window-size=1440,1200',f'--screenshot={out}',f'http://127.0.0.1:{port}/{route}']
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
            if proc.returncode==0 and out.exists(): made.append(out.name)
            else: errors.append(f"{route}: Edge exited {proc.returncode}")
    finally: server.shutdown();server.server_close()
    return made,errors


def safe_add(zf:zipfile.ZipFile,path:Path,arcname:str) -> None:
    if not path.exists() or not path.is_file(): return
    if path.suffix.lower() in {'.pem','.key','.env'}: return
    text=None
    if path.suffix.lower() in {'.json','.html','.js','.css','.txt','.csv','.log','.md'}:
        text=path.read_text(encoding='utf-8',errors='ignore')
        if any(p.search(text) for p in SECRET_PATTERNS): return
    zf.write(path,arcname)


def export_bundle(report:dict[str,Any],screenshots:bool) -> Path:
    EXPORT_DIR.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    out=EXPORT_DIR/f'CRM_Diagnostics_{stamp}.zip'
    with tempfile.TemporaryDirectory(prefix='crm-diag-') as td:
        temp=Path(td); shotdir=temp/'screenshots'
        shot_names=[]; shot_errors=[]
        if screenshots:
            routes=[r['path'] for r in read_json(ROOT/'config'/'routes.json')['routes'] if r.get('primary')]
            shot_names,shot_errors=capture_screenshots(routes,shotdir)
        report['browser_capture']={'screenshots':shot_names,'warnings':shot_errors}
        OUTPUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        manifest={'created_at':utcnow(),'application_version':report['application_version'],'files':[],'redaction':'Secret-like files and values are excluded.'}
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zf:
            selected=['diagnostics.json','system_integrity.json','configuration_reconciliation.json','operating_state.json','version.json','cloud_status.json','threecommas.json','strategies.json','coin_discovery.json','candidate_validation.json','walk_forward_registry.json','research_analytics.json','market_intelligence.json','portfolio_intelligence.json','adaptive_intelligence.json','recommendation_intelligence.json','outcome_intelligence.json','command_state.json']
            for name in selected:
                path=DOCS/name
                if path.exists(): safe_add(zf,path,f'data/{name}');manifest['files'].append(f'data/{name}')
            for p in sorted(shotdir.glob('*.png')):
                zf.write(p,f'screenshots/{p.name}');manifest['files'].append(f'screenshots/{p.name}')
            for name in ['VERSION','app/release.json','config/routes.json','UPDATE_V33.md']:
                path=ROOT/name; safe_add(zf,path,name); manifest['files'].append(name)
            zf.writestr('manifest.json',json.dumps(manifest,indent=2))
    return out


def build_report(full:bool=False) -> dict[str,Any]:
    checks=[check_release(),check_routes(),*html_checks(),*json_checks(),readonly_check(),secret_check(),workflow_automation_check(),*source_checks()]
    if full:
        checks.append(run_command_check('acceptance.tests','Python test suite',[sys.executable,'-m','pytest','-q']))
        checks.append(run_command_check('acceptance.publish','Publication validator',[sys.executable,'scripts/validate_publish.py']))
    required=[c for c in checks if c.required]
    passed=sum(c.passed for c in required)
    score=round(100*passed/max(1,len(required)))
    if any(c.status=='fail' and c.required for c in checks): state='fail'
    elif any(c.status=='warn' for c in checks): state='warning'
    else: state='healthy'
    release=read_json(ROOT/'app'/'release.json')
    return {
        'schema_version':'1.0','application_version':release['version'],'engine':'V33 Diagnostics and Acceptance Engine','generated_at':utcnow(),'host':socket.gethostname(),'platform':sys.platform,'python':sys.version.split()[0],
        'mode':'read_only_observability','overall':{'state':state,'score':score,'required_passed':passed,'required_total':len(required),'warnings':sum(c.status=='warn' for c in checks),'failures':sum(c.status=='fail' for c in checks)},
        'checks':[asdict(c) for c in checks],
        'privacy':{'secrets_included':False,'credentials_included':False,'raw_private_keys_included':False},
    }


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--export',action='store_true');parser.add_argument('--screenshots',action='store_true');args=parser.parse_args()
    report=build_report(args.full);OUTPUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Diagnostics: {report['overall']['state'].upper()} - {report['overall']['score']}%")
    for c in report['checks']: print(f"[{c['status'].upper():4}] {c['name']}: {c['message']}")
    if args.export:
        out=export_bundle(report,args.screenshots);print(f"Export created: {out}")
    return 1 if report['overall']['state']=='fail' else 0

if __name__=='__main__': raise SystemExit(main())
