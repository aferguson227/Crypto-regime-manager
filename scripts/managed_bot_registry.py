#!/usr/bin/env python3
"""Persistent My Bots registry.

Authoritative membership lives outside Git in CRM_Data/Runtime/State.
The published docs snapshot is only a read-only projection for the dashboard.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.runtime_state_manager import state_dir

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'managed_bot_registry.json'
STATE_NAME='managed_bot_registry.json'

def now():return datetime.now(timezone.utc).isoformat()
def spath():return state_dir()/STATE_NAME
def load_json(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def normalize_asset(v):return str(v or '').upper().replace('/USDT','').replace('-USDT','').strip()
def current():
 d=load_json(spath(),{'assets':[]})
 assets=sorted({normalize_asset(x) for x in d.get('assets') or [] if normalize_asset(x)})
 return {'schema_version':'1.0','application_version':application_version(),'updated_at':d.get('updated_at') or now(),'assets':assets}
def save(assets,reason='user'):
 d={'schema_version':'1.0','application_version':application_version(),'updated_at':now(),'reason':reason,
    'assets':sorted({normalize_asset(x) for x in assets if normalize_asset(x)})}
 spath().parent.mkdir(parents=True,exist_ok=True);spath().write_text(json.dumps(d,indent=2),encoding='utf-8')
 OUT.write_text(json.dumps(d,indent=2),encoding='utf-8')
 return d
def seed():
 if spath().exists():
  d=current();OUT.write_text(json.dumps(d,indent=2),encoding='utf-8');return d
 # One-time migration: keep currently validated paper candidates so an upgrade
 # does not unexpectedly empty My Bots.
 life=load_json(DOCS/'deployment_lifecycle.json');paper=load_json(DOCS/'paper_portfolio.json')
 paper_assets={normalize_asset(x.get('asset')) for x in paper.get('bots') or []}
 assets=[]
 for x in life.get('bots') or []:
  a=normalize_asset(x.get('asset'))
  if a in paper_assets and x.get('dca_optimisation_status')=='COMPLETE':
   assets.append(a)
 return save(assets,'migration_seed')
def add(asset):
 d=current();return save(d['assets']+[normalize_asset(asset)],'user_add')
def remove(asset):
 a=normalize_asset(asset);d=current();return save([x for x in d['assets'] if x!=a],'user_remove')
def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd')
 sub.add_parser('seed');sub.add_parser('list')
 for cmd in ('add','remove'):
  p=sub.add_parser(cmd);p.add_argument('asset')
 a=ap.parse_args();cmd=a.cmd or 'seed'
 d=seed() if cmd=='seed' else current()
 if cmd=='add':d=add(a.asset)
 elif cmd=='remove':d=remove(a.asset)
 elif cmd=='list':OUT.write_text(json.dumps(d,indent=2),encoding='utf-8')
 print(json.dumps(d,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
