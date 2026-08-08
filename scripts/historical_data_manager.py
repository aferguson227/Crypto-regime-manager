#!/usr/bin/env python3
"""V47 KuCoin public historical-data acquisition and continuity manager.

Raw candles live outside Git by default. The Local Agent performs bounded,
incremental acquisition; installers and CI only report the plan unless --sync
or CRM_KUCOIN_HISTORY_SYNC=1 is supplied.
"""
from __future__ import annotations
import argparse,csv,json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'historical_data_status.json'
POLICY_PATH=ROOT/'config'/'kucoin_research_policy.json'

def load_json(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default

def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 if raw:return Path(raw)
 if os.name=='nt':return Path(r'C:\Crypto\CRM_Data')
 return Path.home()/'.crypto_regime_manager_data'

def history_dir():return data_root()/'KuCoin'/'4h'
def file_for(symbol):return history_dir()/(symbol.upper().replace('/','-')+'_4H.csv')

def parse_rows(path):
 rows={}
 if not path.exists():return rows
 with path.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   try:rows[int(datetime.fromisoformat(r['time'].replace('Z','+00:00')).timestamp())]=r
   except:pass
 return rows

def save_rows(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f);w.writerow(['time','open','high','low','close','volume','trades'])
  for ts,r in sorted(rows.items()):
   t=datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace('+00:00','Z')
   w.writerow([t,r['open'],r['high'],r['low'],r['close'],r.get('volume',0),r.get('trades',0)])

def fetch(symbol,start_at,end_at,policy):
 params=urllib.parse.urlencode({'symbol':symbol,'type':'4hour','startAt':int(start_at),'endAt':int(end_at)})
 req=urllib.request.Request('https://api.kucoin.com/api/v1/market/candles?'+params,headers={'User-Agent':'Crypto-Regime-Manager/47.0','Accept':'application/json'})
 last=None
 for attempt in range(int(policy.get('request_retries',3))):
  try:
   with urllib.request.urlopen(req,timeout=30) as resp:payload=json.loads(resp.read().decode('utf-8'))
   if payload.get('code')!='200000' or not isinstance(payload.get('data'),list):raise RuntimeError(f'Unexpected KuCoin response code={payload.get("code")}')
   now=int(time.time());out={}
   for x in payload['data']:
    ts=int(x[0])
    if ts+14400>now:continue
    out[ts]={'open':float(x[1]),'close':float(x[2]),'high':float(x[3]),'low':float(x[4]),'volume':float(x[5]),'trades':0}
   return out
  except Exception as exc:
   last=exc;time.sleep(min(4,1+attempt))
 raise RuntimeError(str(last))

def candidate_symbols():
 disc=load_json(DOCS/'coin_discovery.json');uni=load_json(DOCS/'coin_universe.json');p=load_json(POLICY_PATH)
 seen=[];usdt=[]
 for x in (disc.get('researched_candidates') or [])+(disc.get('shortlist') or []):
  s=str(x.get('symbol') or '').upper()
  if s.endswith('-USDT') and s not in seen:seen.append(s);usdt.append(s)
 usdt=usdt[:int(p.get('deep_research_usdt_assets',8))]
 # Experimental BTC pairs only for bases already serious enough to be in the USDT research list.
 allrows=uni.get('candidates') or [];available={str(x.get('symbol') or '').upper() for x in allrows}
 btc=[]
 for s in usdt:
  b=s.split('-')[0]+'-BTC'
  if b in available:btc.append(b)
 btc=btc[:int(p.get('experimental_btc_assets',3))]
 # BTC-USDT is always useful as universal regime evidence when it exists on KuCoin.
 if 'BTC-USDT' not in usdt:usdt.insert(0,'BTC-USDT')
 return usdt,btc

def sync_symbol(symbol,policy):
 path=file_for(symbol);rows=parse_rows(path);seconds=14400;limit=int(policy.get('candles_per_request',1500));span=seconds*(limit-1)
 now=int(time.time())//seconds*seconds
 before=len(rows);pages=0;errors=[]
 # Latest/forward page first.
 latest=max(rows) if rows else None
 start=max(0,(latest-seconds if latest else now-span))
 try:
  rows.update(fetch(symbol,start,now,policy));pages+=1
 except Exception as exc:errors.append('forward: '+str(exc))
 # Backfill bounded pages.
 maxpages=int(policy.get('backfill_pages_per_symbol_per_cycle',2))
 complete=False
 for _ in range(maxpages):
  if not rows:break
  earliest=min(rows);end=earliest-seconds
  if end<=0:complete=True;break
  start=max(0,end-span)
  try:
   got=fetch(symbol,start,end,policy);pages+=1
   if not got:complete=True;break
   old=len(rows);rows.update(got)
   if len(got)<limit or len(rows)==old:complete=True
   time.sleep(float(policy.get('request_pause_seconds',.25)))
  except Exception as exc:errors.append('backfill: '+str(exc));break
 if rows:save_rows(path,rows)
 earliest=min(rows) if rows else None;latest=max(rows) if rows else None
 return {'symbol':symbol,'quote':symbol.split('-')[-1],'file':str(path),'bars':len(rows),'new_bars':len(rows)-before,'pages_requested':pages,
  'earliest':datetime.fromtimestamp(earliest,tz=timezone.utc).isoformat() if earliest else None,
  'latest':datetime.fromtimestamp(latest,tz=timezone.utc).isoformat() if latest else None,
  'backfill_complete':complete,'errors':errors,'status':'ERROR' if errors and not rows else ('PARTIAL' if errors else 'OK')}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--sync',action='store_true');args=ap.parse_args()
 p=load_json(POLICY_PATH);usdt,btc=candidate_symbols();symbols=usdt+btc;do_sync=args.sync or os.getenv('CRM_KUCOIN_HISTORY_SYNC')=='1'
 existing={x:file_for(x) for x in symbols};results=[]
 if do_sync:
  maxn=int(p.get('symbols_per_local_agent_cycle',5))
  # Prioritise the shortest histories so backfill progresses fairly across assets.
  ordered=sorted(symbols,key=lambda s:len(parse_rows(existing[s])))
  for s in ordered[:maxn]:
   try:results.append(sync_symbol(s,p))
   except Exception as exc:results.append({'symbol':s,'status':'ERROR','errors':[str(exc)],'bars':len(parse_rows(existing[s]))})
 # Report every tracked symbol, even if not touched this cycle.
 touched={x['symbol']:x for x in results}
 inventory=[]
 for s in symbols:
  if s in touched:inventory.append(touched[s]);continue
  rows=parse_rows(file_for(s));ks=sorted(rows)
  inventory.append({'symbol':s,'quote':s.split('-')[-1],'file':str(file_for(s)),'bars':len(rows),'new_bars':0,'pages_requested':0,
   'earliest':datetime.fromtimestamp(ks[0],tz=timezone.utc).isoformat() if ks else None,'latest':datetime.fromtimestamp(ks[-1],tz=timezone.utc).isoformat() if ks else None,
   'backfill_complete':False,'errors':[],'status':'CACHED' if rows else 'QUEUED'})
 minbars=int(p.get('minimum_backtest_bars',900));ready=sum(1 for x in inventory if x.get('bars',0)>=minbars)
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'provider':'KuCoin public spot candles','autonomous_discovery_source':'Full KuCoin USDT scan -> ranked shortlist -> bounded historical acquisition',
  'mode':'bounded_incremental_acquisition' if do_sync else 'plan_only','data_root':str(data_root()),'target_timeframe':'4hour',
  'production_research':{'quote':'USDT','symbols':usdt,'count':len(usdt)},'experimental_research':{'quote':'BTC','symbols':btc,'count':len(btc),'execution_allowed':False},
  'minimum_backtest_bars':minbars,'candidate_count':len(symbols),'research_ready_count':ready,'inventory':inventory,
  'progress_pct':round(100*ready/len(symbols),1) if symbols else 0,
  'status':'ACTIVE' if do_sync else ('READY' if symbols else 'WAITING_FOR_DISCOVERY'),
  'continuity_policy':'append completed candles, backfill older history incrementally, deduplicate timestamps, keep raw research data outside Git',
  'note':'Local Agent downloads only a bounded number of pages per cycle. New candidates nominated by the hourly full KuCoin USDT scan enter this queue automatically. Full-history depth grows without blocking the 15-minute refresh.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Historical data status written: {OUT}; mode={payload["mode"]}; ready={ready}/{len(symbols)}');return 0
if __name__=='__main__':raise SystemExit(main())
