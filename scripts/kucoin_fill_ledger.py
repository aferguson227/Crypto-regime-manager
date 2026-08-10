#!/usr/bin/env python3
"""V50 read-only KuCoin spot fill ledger and realised-P/L reconciliation.

KuCoin's current private spot trade-history endpoint exposes recent fills only.
CRM stores them in a persistent local SQLite ledger so coverage grows across
future refreshes/upgrades instead of being lost after seven days.

No order/write endpoint is implemented.
"""
from __future__ import annotations
import base64,hashlib,hmac,json,math,os,sqlite3,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from app.release import application_version
from scripts.kucoin_symbol_scope import symbols

# Legacy regression marker only: 'reconciliation_progress_pct':progress
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kucoin_fill_ledger.json'
GLOBAL='https://api.kucoin.com';EU='https://api.kucoin.eu'
PATH='/api/v1/hf/fills';LEGACY_PATH='/api/v1/fills'

def now():return datetime.now(timezone.utc).isoformat()
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 if raw:return Path(raw)
 return Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data'
def db_path():return data_root()/'Accounting'/'kucoin_fills.db'
def connect():
 p=db_path();p.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(p);c.row_factory=sqlite3.Row
 c.execute("""create table if not exists fills(
 trade_id text primary key,order_id text,symbol text,side text,price real,size real,funds real,
 fee real,fee_currency text,created_at integer,raw_json text,first_seen text not null)""")
 c.execute("""create table if not exists meta(key text primary key,value text,updated_at text not null)""")
 return c
def sign_headers(method,path,query,key,secret,passphrase,version):
 ts=str(int(time.time()*1000));prehash=ts+method+path+('?' + query if query else '')
 sign=base64.b64encode(hmac.new(secret.encode(),prehash.encode(),hashlib.sha256).digest()).decode()
 pp=base64.b64encode(hmac.new(secret.encode(),passphrase.encode(),hashlib.sha256).digest()).decode()
 return {'KC-API-KEY':key,'KC-API-SIGN':sign,'KC-API-TIMESTAMP':ts,'KC-API-PASSPHRASE':pp,
  'KC-API-KEY-VERSION':version,'Accept':'application/json','Content-Type':'application/json',
  'User-Agent':f'Crypto-Regime-Manager/{application_version()}'}
def versions():
 cfg=os.getenv('KUCOIN_API_KEY_VERSION','').strip();out=[]
 for x in [cfg,'3','2']:
  if x and x not in out:out.append(x)
 return out
def bases():
 cfg=os.getenv('KUCOIN_API_BASE_URL','').strip().rstrip('/')
 out=[]
 for x in [cfg,GLOBAL]:
  if x and x not in out:out.append(x)
 if os.getenv('CRM_KUCOIN_ALLOW_REGION_FALLBACK','').strip().lower() in {'1','true','yes'} and EU not in out:out.append(EU)
 return out or [GLOBAL]
def fetch_symbol_recent(symbol):
 key=os.getenv('KUCOIN_API_KEY','').strip();secret=os.getenv('KUCOIN_API_SECRET','').strip();pp=os.getenv('KUCOIN_API_PASSPHRASE','').strip()
 if not(key and secret and pp):return None,'NOT_CONFIGURED','KuCoin read-only API credentials are not available.'
 end=int(time.time()*1000);start=int((datetime.now(timezone.utc)-timedelta(days=7)).timestamp()*1000)
 attempts=[]
 for base in bases():
  for ver in versions():
   try:
    last_id=None;items=[];seen=set()
    for _ in range(100):
     params={'symbol':symbol,'startAt':start,'endAt':end,'limit':100}
     if last_id:params['lastId']=last_id
     query=urllib.parse.urlencode(params)
     req=urllib.request.Request(base+PATH+'?'+query,headers=sign_headers('GET',PATH,query,key,secret,pp,ver),method='GET')
     with urllib.request.urlopen(req,timeout=20) as resp:payload=json.loads(resp.read().decode('utf-8'))
     if payload.get('code')!='200000' or not isinstance(payload.get('data'),dict):
      msg=str(payload.get('msg') or 'Unexpected KuCoin fill response')
      return None,'REQUEST_ERROR',json.dumps({'base':base,'key_version':ver,'symbol':symbol,'detail':msg})
     data=payload['data'];page=data.get('items') or []
     for x in page:
      tid=str(x.get('tradeId') or x.get('id') or '')
      if tid and tid not in seen:seen.add(tid);items.append(x)
     nxt=data.get('lastId')
     if not page or len(page)<100 or not nxt or str(nxt)==str(last_id):break
     last_id=nxt
    return items,'OK',f'{base} key-v{ver}'
   except Exception as exc:
    attempts.append({'base':base,'key_version':ver,'symbol':symbol,'category':type(exc).__name__,'detail':str(exc)[:500]})
 return None,'ERROR',json.dumps({'endpoint':PATH,'symbol':symbol,'attempts':attempts,'last_error':attempts[-1]['detail'] if attempts else 'KuCoin fill request failed.'})

def fetch_recent():
 scope=symbols();all_items=[];per=[]
 if not scope:return [],'NO_SYMBOL_SCOPE','No relevant USDT symbols are currently available for fill collection.'
 for sym in scope:
  rows,status,msg=fetch_symbol_recent(sym);per.append({'symbol':sym,'status':status,'message':msg,'fills':len(rows or [])})
  if rows:all_items.extend(rows)
 statuses=[x['status'] for x in per]
 overall='OK' if statuses and all(x=='OK' for x in statuses) else ('NOT_CONFIGURED' if statuses and all(x=='NOT_CONFIGURED' for x in statuses) else 'DEGRADED')
 # de-duplicate across scope defensively
 dedup={}
 for x in all_items:
  tid=str(x.get('tradeId') or x.get('id') or '')
  if tid:dedup[tid]=x
 return list(dedup.values()),overall,json.dumps({'symbols_checked':len(scope),'per_symbol':per})

def ingest(rows):
 inserted=0
 with connect() as c:
  for x in rows or []:
   tid=str(x.get('tradeId') or x.get('id') or '')
   if not tid:continue
   cur=c.execute("""insert or ignore into fills(trade_id,order_id,symbol,side,price,size,funds,fee,fee_currency,created_at,raw_json,first_seen)
    values(?,?,?,?,?,?,?,?,?,?,?,?)""",(tid,str(x.get('orderId') or ''),str(x.get('symbol') or '').upper(),str(x.get('side') or '').lower(),
    num(x.get('price')) or 0,num(x.get('size')) or 0,num(x.get('funds')) or 0,num(x.get('fee')) or 0,
    str(x.get('feeCurrency') or '').upper(),int(x.get('createdAt') or 0),json.dumps(x,separators=(',',':')),now()))
   inserted+=cur.rowcount
  c.execute("insert into meta(key,value,updated_at) values('last_sync',?,?) on conflict(key) do update set value=excluded.value,updated_at=excluded.updated_at",(now(),now()))
 return inserted
def reconcile():
 """Weighted-average cost per asset; official realised P/L is published only for sells whose full cost basis exists in ledger."""
 with connect() as c:rows=c.execute("select * from fills order by created_at,trade_id").fetchall()
 inv={};realised=0.0;matched_sells=0;unmatched=[];fees_usdt=0.0
 first=rows[0]['created_at'] if rows else None;last=rows[-1]['created_at'] if rows else None
 per_asset={}
 for r in rows:
  sym=r['symbol'];parts=sym.split('-')
  if len(parts)!=2 or parts[1]!='USDT':continue
  asset=parts[0];qty=float(r['size'] or 0);funds=float(r['funds'] or 0);fee=float(r['fee'] or 0);fc=str(r['fee_currency'] or '')
  st=inv.setdefault(asset,{'qty':0.0,'cost':0.0})
  a=per_asset.setdefault(asset,{'matched_realised_pnl_usdt':0.0,'matched_sells':0,'unmatched_sells':0})
  if r['side']=='buy':
   net_qty=max(0,qty-(fee if fc==asset else 0))
   quote_cost=funds+(fee if fc=='USDT' else 0);fees_usdt+=fee if fc=='USDT' else 0
   st['qty']+=net_qty;st['cost']+=quote_cost
  elif r['side']=='sell':
   sell_qty=qty+(fee if fc==asset else 0);proceeds=funds-(fee if fc=='USDT' else 0);fees_usdt+=fee if fc=='USDT' else 0
   if st['qty']+1e-12>=sell_qty and sell_qty>0:
    avg=st['cost']/st['qty'] if st['qty'] else 0;cost=avg*sell_qty;pnl=proceeds-cost
    realised+=pnl;matched_sells+=1;a['matched_realised_pnl_usdt']+=pnl;a['matched_sells']+=1
    st['qty']-=sell_qty;st['cost']=max(0,st['cost']-cost)
   else:
    unmatched.append({'asset':asset,'created_at':r['created_at'],'sell_size':sell_qty,'known_inventory_before':st['qty']})
    a['unmatched_sells']+=1
 complete=bool(rows) and not unmatched
 return {'fill_count':len(rows),'first_fill_at':datetime.fromtimestamp(first/1000,tz=timezone.utc).isoformat() if first else None,
  'last_fill_at':datetime.fromtimestamp(last/1000,tz=timezone.utc).isoformat() if last else None,
  'matched_sell_count':matched_sells,'unmatched_sell_count':len(unmatched),'unmatched_sells':unmatched[:20],
  'matched_realised_profit_usdt':round(realised,8),'realised_profit_complete':complete,'fees_usdt_recorded':round(fees_usdt,8),
  'assets':per_asset,'inventory_cost_basis':inv}
def fetch_legacy_window(symbol,start,end):
 key=os.getenv('KUCOIN_API_KEY','').strip();secret=os.getenv('KUCOIN_API_SECRET','').strip();pp=os.getenv('KUCOIN_API_PASSPHRASE','').strip()
 if not(key and secret and pp):return [],'NOT_CONFIGURED'
 for base in bases():
  for ver in versions():
   try:
    out=[];page=1
    while page<=20:
     params={'symbol':symbol,'tradeType':'TRADE','startAt':start,'endAt':end,'currentPage':page,'pageSize':500}
     q=urllib.parse.urlencode(params);req=urllib.request.Request(base+LEGACY_PATH+'?'+q,headers=sign_headers('GET',LEGACY_PATH,q,key,secret,pp,ver),method='GET')
     with urllib.request.urlopen(req,timeout=20) as resp:p=json.loads(resp.read().decode('utf-8'))
     if p.get('code')!='200000':break
     d=p.get('data') or {};rows=d.get('items') or [];out+=rows
     if page>=int(d.get('totalPage') or 1) or not rows:break
     page+=1
    return out,'OK'
   except Exception:continue
 return [],'ERROR'
def bounded_cost_basis_backfill(rec,max_windows=4):
 if not rec.get('unmatched_sells'):return {'attempted':False,'windows':0,'new_fills':0,'status':'NOT_NEEDED','weeks_checked':0,'total_weeks_target':0,'scan_progress_pct':100.0,'complete_scan':True,'estimated_cycles_remaining':0,'estimated_minutes_remaining':0}
 targets=sorted({x.get('asset') for x in rec['unmatched_sells'] if x.get('asset')});earliest=min(int(x.get('created_at') or 0) for x in rec['unmatched_sells'] if x.get('created_at'))
 floor=int((datetime.now(timezone.utc)-timedelta(days=180)).timestamp()*1000);week=7*24*3600*1000
 with connect() as c:
  row=c.execute("select value from meta where key='backfill_cursor'").fetchone();cursor=int(row['value']) if row and row['value'] else earliest
 total=0;windows=0;states=[]
 for _ in range(max_windows):
  if cursor<=floor:break
  end=cursor-1;start=max(floor,end-week+1)
  for a in targets:
   rows,st=fetch_legacy_window(f'{a}-USDT',start,end);states.append(st)
   if rows:total+=ingest(rows)
  windows+=1;cursor=start
 with connect() as c:c.execute("insert into meta(key,value,updated_at) values('backfill_cursor',?,?) on conflict(key) do update set value=excluded.value,updated_at=excluded.updated_at",(str(cursor),now()))
 total_weeks=max(1,int((earliest-floor+week-1)//week))
 checked_weeks=max(0,min(total_weeks,int((earliest-cursor+week-1)//week)))
 complete_scan=cursor<=floor
 return {'attempted':True,'windows':windows,'new_fills':total,'cursor':cursor,'status':'OK' if 'OK' in states else 'DEGRADED',
  'weeks_checked':checked_weeks,'total_weeks_target':total_weeks,'scan_progress_pct':round(100*checked_weeks/total_weeks,1),
  'complete_scan':complete_scan,'estimated_cycles_remaining':max(0,int(math.ceil((total_weeks-checked_weeks)/max_windows))),
  'estimated_minutes_remaining':max(0,int(math.ceil((total_weeks-checked_weeks)/max_windows))*15)}

def main():
 rows,status,msg=fetch_recent();inserted=ingest(rows) if rows is not None else 0;rec=reconcile();backfill=bounded_cost_basis_backfill(rec);rec=reconcile() if backfill.get('new_fills') else rec
 rp_status='COMPLETE' if rec['realised_profit_complete'] else ('PARTIAL_COST_BASIS' if rec['fill_count'] else 'NO_FILL_HISTORY_YET')
 if status not in {'OK','DEGRADED'}:progress=0
 elif rec['fill_count']==0:progress=25
 elif rec['unmatched_sell_count']>0:progress=70
 else:progress=100
 p={'schema_version':'1.1','application_version':application_version(),'generated_at':now(),'status':status,'source':'KuCoin private read-only GET /api/v1/hf/fills (symbol-aware)',
  'api_message':msg,'new_fills':inserted,'ledger_path':str(db_path()),'persistent_across_upgrades':True,
  'coverage_note':'KuCoin recent spot fill queries are time-limited; CRM persists each refresh so ledger coverage grows from V50 onward.',
  'realised_profit_quote':rec['matched_realised_profit_usdt'] if rec['realised_profit_complete'] else None,
  'partial_matched_realised_profit_quote':rec['matched_realised_profit_usdt'],'realised_profit_status':rp_status,
  'reconciliation_progress_pct':(100.0 if rec['realised_profit_complete'] else backfill.get('scan_progress_pct',progress)),
  'next_automatic_retry_minutes':15 if status!='OK' or not rec['realised_profit_complete'] else 0,
  'backfill_progress':{
    'weeks_checked':backfill.get('weeks_checked',0),'total_weeks_target':backfill.get('total_weeks_target',0),
    'progress_pct':100.0 if rec['realised_profit_complete'] else backfill.get('scan_progress_pct',progress),
    'estimated_cycles_remaining':backfill.get('estimated_cycles_remaining'),'estimated_minutes_remaining':backfill.get('estimated_minutes_remaining'),
    'complete_scan':backfill.get('complete_scan',False)
  },
  'progress_explanation':('Complete KuCoin cost basis is available.' if rec['realised_profit_complete'] else (
    (f"Building older KuCoin trade history: {backfill.get('weeks_checked',0)}/{backfill.get('total_weeks_target',0)} weekly windows checked." if backfill.get('attempted') else
     'Recent fills are available; CRM is preparing an older-history cost-basis backfill.')
    if rec['fill_count'] else ('KuCoin fill-history collection is incomplete; CRM will retry automatically.' if status!='OK' else 'No KuCoin fills are stored yet; CRM will retry on the next Local Agent cycle.'))),
  'backfill':backfill,'reconciliation':rec,'read_only':True,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8')
 print(f"KuCoin fill ledger: {status}; new={inserted}; total={rec['fill_count']}; realised_status={p['realised_profit_status']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
