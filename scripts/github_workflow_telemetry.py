#!/usr/bin/env python3
"""Collect read-only GitHub Actions telemetry using the workflow GITHUB_TOKEN."""
from __future__ import annotations
import json,os,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/workflow_history.json'

def parse_time(v):
    if not v:return None
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception:return None

def main():
    token=os.getenv('GITHUB_TOKEN','').strip(); repo=os.getenv('GITHUB_REPOSITORY','').strip(); api=os.getenv('GITHUB_API_URL','https://api.github.com').rstrip('/')
    if not token or not repo:
        print('GitHub telemetry skipped: GITHUB_TOKEN or GITHUB_REPOSITORY unavailable.')
        return 0
    req=urllib.request.Request(f'{api}/repos/{repo}/actions/runs?per_page=100',headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Crypto-Regime-Manager'})
    with urllib.request.urlopen(req,timeout=30) as r: data=json.loads(r.read().decode('utf-8'))
    rows=[]; now=datetime.now(timezone.utc)
    for x in data.get('workflow_runs') or []:
        created=parse_time(x.get('created_at')); started=parse_time(x.get('run_started_at')); updated=parse_time(x.get('updated_at'))
        queue=(started-created).total_seconds() if created and started else ((now-created).total_seconds() if created and x.get('status')=='queued' else None)
        duration=(updated-started).total_seconds() if started and updated and x.get('status')=='completed' else None
        conclusion=x.get('conclusion'); status=x.get('status')
        if conclusion == 'success':
            normalized = 'success'
        elif conclusion == 'cancelled':
            normalized = 'cancelled'
        elif conclusion == 'failure':
            normalized = 'failure'
        elif status == 'queued':
            normalized = 'queued'
        elif status == 'in_progress':
            normalized = 'in_progress'
        else:
            normalized = conclusion or status
        rows.append({'id':x.get('id'),'name':x.get('name'),'event':x.get('event'),'head_sha':x.get('head_sha'),'status':normalized,'raw_status':status,'conclusion':conclusion,'created_at':x.get('created_at'),'started_at':x.get('run_started_at'),'updated_at':x.get('updated_at'),'queue_seconds':round(queue,1) if queue is not None else None,'duration_seconds':round(duration,1) if duration is not None else None,'html_url':x.get('html_url')})
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now.isoformat(),'runs':rows}
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Workflow telemetry written: {OUT} ({len(rows)} runs)'); return 0
if __name__=='__main__': raise SystemExit(main())
