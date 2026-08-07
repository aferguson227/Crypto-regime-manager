#!/usr/bin/env python3
"""Read-only synchronization intelligence for repository, Pages, Actions and 3Commas."""
from __future__ import annotations
import json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'synchronization_status.json'; POLICY=ROOT/'config/synchronization_policy.json'

def load(path,default=None):
 try:return json.loads(path.read_text(encoding='utf-8-sig'))
 except Exception:return {} if default is None else default

def fetch_json(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Crypto-Regime-Manager-Sync/1.0','Cache-Control':'no-cache'})
  with urllib.request.urlopen(req,timeout=8) as r:return json.loads(r.read().decode('utf-8'))
 except Exception:return None

def age_minutes(ts):
 if not ts:return None
 try:
  d=datetime.fromisoformat(str(ts).replace('Z','+00:00')).astimezone(timezone.utc)
  return round((datetime.now(timezone.utc)-d).total_seconds()/60,1)
 except Exception:return None

def main():
 now=datetime.now(timezone.utc); p=load(POLICY,{}); repo=p.get('repository',''); branch=p.get('branch','main'); pages=p.get('pages_url','').rstrip('/')+'/'
 expected=application_version(); raw=f'https://raw.githubusercontent.com/{repo}/{branch}/docs/version.json' if repo else ''
 remote=fetch_json(raw) if raw else None; live=fetch_json(pages+'version.json') if pages else None
 gh=load(DOCS/'github_actions_health.json',{}); op=load(DOCS/'operational_health.json',{}); tc=load(DOCS/'threecommas.json',{})
 rv=(remote or {}).get('version') or (remote or {}).get('application_version'); lv=(live or {}).get('version') or (live or {}).get('application_version')
 def vt(v):
  try:return tuple(int(x) for x in str(v).split('.'))
  except Exception:return ()
 def version_state(v,kind):
  if v is None:return 'UNKNOWN'
  if v==expected:return 'SYNCED'
  if vt(v) and vt(expected) and vt(v)<vt(expected):return 'PENDING_PUSH' if kind=='github' else 'PENDING_PUBLICATION'
  return 'DRIFT'
 tc_age=age_minutes(tc.get('generated_at') or (op.get('threecommas') or {}).get('last_success_at'))
 app_age=age_minutes((op.get('application') or {}).get('last_success_at'))
 components={
  'release':{'status':'SYNCED','expected_version':expected},
  'github_main':{'status':version_state(rv,'github'),'version':rv,'expected_version':expected},
  'live_pages':{'status':version_state(lv,'live'),'version':lv,'expected_version':expected,'url':pages},
  'github_actions':{'status':'HEALTHY' if gh.get('state')=='HEALTHY' else (gh.get('state') or 'UNKNOWN'),'workflow_count':gh.get('workflow_count')},
  'threecommas':{'status':str(tc.get('status') or (op.get('threecommas') or {}).get('status') or 'UNKNOWN').upper(),'age_minutes':tc_age},
  'application_refresh':{'status':str((op.get('application') or {}).get('cloud_state') or 'UNKNOWN').upper(),'age_minutes':app_age}
 }
 known=[x['status'] for x in components.values() if x['status']!='UNKNOWN']
 if any(x in {'DRIFT','CRITICAL','FAIL','FAILURE'} for x in known): overall='DRIFT'
 elif any(x in {'PENDING_PUSH','PENDING_PUBLICATION'} for x in known): overall='PENDING_PUBLICATION'
 elif any(x in {'WARNING','PARTIAL','STALE','DEGRADED'} for x in known): overall='ATTENTION'
 elif known and all(x in {'SYNCED','HEALTHY','OK'} for x in known): overall='SYNCHRONIZED'
 else: overall='CHECKING'
 payload={'schema_version':'1.0','application_version':expected,'generated_at':now.isoformat(),'overall':overall,'components':components,'sources':{'github_main_version_url':raw,'live_version_url':pages+'version.json' if pages else ''},'network_checks':{'github_main_available':remote is not None,'live_pages_available':live is not None},'guardrails':{'read_only':True,'no_remote_changes':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Synchronization status written: {OUT} ({overall})'); return 0
if __name__=='__main__': raise SystemExit(main())
