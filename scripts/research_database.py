#!/usr/bin/env python3
"""V49 persistent research database.

The DB is stored outside Git so research state, candidate history and cache
metadata survive CRM upgrades. Raw candles remain in the existing KuCoin cache.
"""
from __future__ import annotations
import argparse,json,os,sqlite3
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config'/'v49_autonomy_policy.json'
DOCS=ROOT/'docs'
STATUS=DOCS/'research_database_status.json'

def now():return datetime.now(timezone.utc).isoformat()
def load(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 if raw:return Path(raw)
 if os.name=='nt':return Path(r'C:\Crypto\CRM_Data')
 return Path.home()/'.crypto_regime_manager_data'
def db_path():
 p=load(POLICY);return data_root()/str(p.get('database_relative_path') or 'Research/crm_research.db')
def connect():
 p=db_path();p.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(p);c.row_factory=sqlite3.Row
 return c
SCHEMA=[
"""create table if not exists meta(key text primary key,value text not null,updated_at text not null)""",
"""create table if not exists assets(
 asset text not null,pair text primary key,quote text not null,
 first_seen text,last_seen text,last_rank integer,last_score real,
 state text,reason text,updated_at text not null)""",
"""create table if not exists cache(
 cache_key text primary key,fingerprint text not null,result_json text,
 created_at text not null,updated_at text not null,duration_seconds real default 0)""",
"""create table if not exists research_runs(
 id integer primary key autoincrement,kind text not null,started_at text not null,
 finished_at text,status text,fingerprint text,assets integer default 0,
 backtests integer default 0,duration_seconds real default 0,message text)""",
"""create table if not exists candidate_state(
 asset text primary key,pair text,state text,readiness_pct real,
 current_regime text,last_research_at text,last_walk_forward_at text,
 recommendation text,updated_at text not null)""",
"""create table if not exists recommendations(
 id integer primary key autoincrement,asset text,pair text,state text,
 confidence_pct real,allocation_usdt real,evidence_json text,
 recorded_at text not null)"""
]
def migrate():
 with connect() as c:
  for sql in SCHEMA:c.execute(sql)
  c.execute("insert into meta(key,value,updated_at) values('schema_version','1',?) on conflict(key) do update set value='1',updated_at=excluded.updated_at",(now(),))
  c.execute("insert into meta(key,value,updated_at) values('application_version',?,?) on conflict(key) do update set value=excluded.value,updated_at=excluded.updated_at",(application_version(),now()))
 write_status()
def set_meta(key,value):
 with connect() as c:c.execute("insert into meta(key,value,updated_at) values(?,?,?) on conflict(key) do update set value=excluded.value,updated_at=excluded.updated_at",(key,str(value),now()))
def get_meta(key,default=None):
 with connect() as c:
  r=c.execute("select value from meta where key=?",(key,)).fetchone()
 return r['value'] if r else default
def cache_get(key,fingerprint):
 with connect() as c:r=c.execute("select * from cache where cache_key=? and fingerprint=?",(key,fingerprint)).fetchone()
 if not r:return None
 try:return json.loads(r['result_json']) if r['result_json'] else {}
 except:return None
def cache_put(key,fingerprint,result,duration=0):
 ts=now()
 with connect() as c:c.execute("""insert into cache(cache_key,fingerprint,result_json,created_at,updated_at,duration_seconds)
 values(?,?,?,?,?,?) on conflict(cache_key) do update set fingerprint=excluded.fingerprint,result_json=excluded.result_json,
 updated_at=excluded.updated_at,duration_seconds=excluded.duration_seconds""",(key,fingerprint,json.dumps(result),ts,ts,float(duration or 0)))
def record_assets():
 disc=load(DOCS/'coin_discovery.json'); rows=(disc.get('shortlist') or [])+(disc.get('researched_candidates') or [])
 ts=now()
 with connect() as c:
  for x in rows:
   pair=str(x.get('symbol') or '').upper()
   if not pair:continue
   asset=str(x.get('base_currency') or pair.split('-')[0]).upper()
   quote=str(x.get('quote_currency') or (pair.split('-')[-1] if '-' in pair else 'USDT')).upper()
   c.execute("""insert into assets(asset,pair,quote,first_seen,last_seen,last_rank,last_score,state,reason,updated_at)
    values(?,?,?,?,?,?,?,?,?,?) on conflict(pair) do update set last_seen=excluded.last_seen,last_rank=excluded.last_rank,
    last_score=excluded.last_score,state=excluded.state,reason=excluded.reason,updated_at=excluded.updated_at""",
    (asset,pair,quote,ts,ts,x.get('rank'),x.get('research_score'),'DISCOVERED',
     '; '.join(x.get('reasons') or [])[:500],ts))
def import_candidate_state():
 wf=load(DOCS/'kucoin_walk_forward.json'); opt=load(DOCS/'optimisation_queue.json')
 byopt={str(x.get('asset') or '').upper():x for x in opt.get('items') or []}
 ts=now()
 with connect() as c:
  for x in wf.get('assets') or []:
   a=str(x.get('asset') or '').upper()
   if not a:continue
   o=byopt.get(a) or {}
   state=str(x.get('status') or o.get('status') or 'RESEARCH_PENDING')
   ready=100.0 if state=='READY_FOR_MANUAL_REVIEW' else float(x.get('progress_pct') or 40 if x.get('bars') else 10)
   c.execute("""insert into candidate_state(asset,pair,state,readiness_pct,current_regime,last_research_at,last_walk_forward_at,recommendation,updated_at)
    values(?,?,?,?,?,?,?,?,?) on conflict(asset) do update set pair=excluded.pair,state=excluded.state,readiness_pct=excluded.readiness_pct,
    current_regime=excluded.current_regime,last_research_at=excluded.last_research_at,last_walk_forward_at=excluded.last_walk_forward_at,
    recommendation=excluded.recommendation,updated_at=excluded.updated_at""",
    (a,x.get('pair') or f'{a}-USDT',state,ready,x.get('current_regime_family'),ts,ts,o.get('next_action'),ts))
def write_status():
 p=db_path()
 with connect() as c:
  counts={
   'known_assets':c.execute("select count(*) n from assets").fetchone()['n'],
   'cached_results':c.execute("select count(*) n from cache").fetchone()['n'],
   'candidate_states':c.execute("select count(*) n from candidate_state").fetchone()['n'],
   'research_runs':c.execute("select count(*) n from research_runs").fetchone()['n'],
  }
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),
  'database_path':str(p),'exists':p.exists(),'size_bytes':p.stat().st_size if p.exists() else 0,
  **counts,'persistent_across_upgrades':True,'status':'READY'}
 STATUS.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 return payload
def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',nargs='?',default='migrate',choices=['migrate','status','import'])
 a=ap.parse_args()
 migrate()
 # V50 reconciliation: seed persistent memory from already-published discovery/research state
 # during every migration/status pass so upgrades never show an empty DB beside populated histories.
 record_assets();import_candidate_state()
 p=write_status();print(f"Research database: {p['status']} · assets={p['known_assets']} · cache={p['cached_results']} · {p['database_path']}");return 0
if __name__=='__main__':raise SystemExit(main())
