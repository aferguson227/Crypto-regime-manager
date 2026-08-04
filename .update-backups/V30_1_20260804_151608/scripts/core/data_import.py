from __future__ import annotations
import csv, json, math, re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

ALIASES={
 'time':['time','timestamp','date','datetime','open_time','unix','epoch'],
 'open':['open','o'],'high':['high','h'],'low':['low','l'],'close':['close','c'],
 'volume':['volume','vol','v','base_volume'],'trades':['trades','count','trade_count']}

@dataclass
class ImportResult:
 exchange:str; symbol:str; source_timeframe_minutes:int; target_timeframe_minutes:int
 rows_in:int; rows_out:int; dropped_rows:int; missing_source_intervals:int
 start:str|None; end:str|None; output_path:str|None=None
 def as_dict(self): return self.__dict__.copy()

def _norm(s:str)->str:return re.sub(r'[^a-z0-9]+','_',str(s).strip().lower()).strip('_')
def _map(headers:Iterable[str])->dict[str,str]:
 n={_norm(h):h for h in headers}; out={}
 for key,vals in ALIASES.items():
  for v in vals:
   if v in n: out[key]=n[v]; break
 return out

def _time(v:Any)->datetime:
 s=str(v).strip()
 if re.fullmatch(r'\d+(\.\d+)?',s):
  x=float(s)
  if x>1e15:x/=1e9
  elif x>1e12:x/=1e3
  elif x<100000: # Excel serial
   return datetime.fromtimestamp((x-25569)*86400,tz=timezone.utc)
  return datetime.fromtimestamp(x,tz=timezone.utc)
 s=s.replace('Z','+00:00')
 try:d=datetime.fromisoformat(s)
 except ValueError:
  for f in ('%Y-%m-%d %H:%M:%S','%Y/%m/%d %H:%M:%S','%d/%m/%Y %H:%M','%Y-%m-%d'):
   try:d=datetime.strptime(s,f);break
   except ValueError:pass
  else:raise
 return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)

def identify_exchange(headers:Iterable[str],filename:str='')->str:
 text=' '.join(map(str,headers)).lower()+' '+filename.lower()
 if 'kraken' in text:return 'Kraken'
 if 'kucoin' in text:return 'KuCoin'
 if 'binance' in text or 'open_time' in text:return 'Binance'
 if 'coinbase' in text:return 'Coinbase'
 if 'tradingview' in text:return 'TradingView'
 return 'Generic OHLCV'

def identify_symbol(filename:str,rows:list[dict[str,Any]])->str:
 for k in ('symbol','pair','ticker'):
  if rows and k in {_norm(x):x for x in rows[0]}:
   original={_norm(x):x for x in rows[0]}[k]; val=str(rows[0].get(original,'')).strip()
   if val:return val.upper().replace('/','-')
 m=re.search(r'([A-Z0-9]{2,12})[-_]?((?:USD|USDT|USDC|EUR|GBP))',Path(filename).stem.upper())
 return f'{m.group(1)}-{m.group(2)}' if m else Path(filename).stem.upper()

def load_csv(path:Path)->tuple[list[dict[str,Any]],dict[str,str]]:
 with path.open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f); rows=list(reader); mapping=_map(reader.fieldnames or [])
 required={'time','open','high','low','close'}
 if not required.issubset(mapping): raise ValueError(f'Missing OHLCV columns: {sorted(required-set(mapping))}')
 return rows,mapping

def normalize(rows:list[dict[str,Any]],m:dict[str,str])->list[dict[str,Any]]:
 out=[]
 for r in rows:
  try:
   d={'time':_time(r[m['time']]),'open':float(r[m['open']]),'high':float(r[m['high']]),'low':float(r[m['low']]),'close':float(r[m['close']]),'volume':float(r.get(m.get('volume',''),0) or 0),'trades':int(float(r.get(m.get('trades',''),0) or 0))}
   if min(d['open'],d['high'],d['low'],d['close'])<=0:continue
   out.append(d)
  except Exception:continue
 return sorted({x['time']:x for x in out}.values(),key=lambda x:x['time'])

def timeframe_minutes(rows:list[dict[str,Any]])->int:
 diffs=[(b['time']-a['time']).total_seconds()/60 for a,b in zip(rows,rows[1:]) if b['time']>a['time']]
 if not diffs:return 0
 return max(1,int(round(median(diffs))))

def resample(rows:list[dict[str,Any]],minutes:int=240)->list[dict[str,Any]]:
 buckets={}; seconds=minutes*60
 for r in rows:
  ts=int(r['time'].timestamp()); key=ts-ts%seconds; buckets.setdefault(key,[]).append(r)
 out=[]
 for key,grp in sorted(buckets.items()):
  grp.sort(key=lambda x:x['time']); out.append({'time':datetime.fromtimestamp(key,tz=timezone.utc),'open':grp[0]['open'],'high':max(x['high'] for x in grp),'low':min(x['low'] for x in grp),'close':grp[-1]['close'],'volume':sum(x['volume'] for x in grp),'trades':sum(x['trades'] for x in grp)})
 return out

def import_file(path:Path,out_dir:Path,target_minutes:int=240)->ImportResult:
 raw,m=load_csv(path); rows=normalize(raw,m); src=timeframe_minutes(rows)
 if src<=0:raise ValueError('Could not determine timeframe')
 if src>target_minutes or target_minutes%src:raise ValueError(f'{src}m data cannot be safely converted to {target_minutes}m')
 converted=resample(rows,target_minutes) if src!=target_minutes else rows
 out_dir.mkdir(parents=True,exist_ok=True); symbol=identify_symbol(path.name,raw); dest=out_dir/f'{symbol.replace("-","")}_{target_minutes//60}H.csv'
 with dest.open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['time','open','high','low','close','volume','trades'])
  for x in converted:w.writerow([x['time'].isoformat().replace('+00:00','Z'),x['open'],x['high'],x['low'],x['close'],x['volume'],x['trades']])
 expected=src*60; gaps=sum(1 for a,b in zip(rows,rows[1:]) if (b['time']-a['time']).total_seconds()>expected*1.5)
 return ImportResult(identify_exchange(raw[0].keys() if raw else [],path.name),symbol,src,target_minutes,len(raw),len(converted),len(raw)-len(rows),gaps,converted[0]['time'].isoformat() if converted else None,converted[-1]['time'].isoformat() if converted else None,str(dest))

def run_import_queue(root:Path)->dict[str,Any]:
 inbox=root/'data'/'imports'; output=root/'data'/'normalized'; reports=[]
 if inbox.exists():
  for p in sorted(inbox.glob('*.csv')):
   try: reports.append({'status':'READY',**import_file(p,output).as_dict(),'source_file':p.name})
   except Exception as e: reports.append({'status':'ERROR','source_file':p.name,'error':str(e)})
 payload={'version':'29.0.0','generated_at':datetime.now(timezone.utc).isoformat(),'target_timeframe':'4h','files':reports,'ready':sum(x['status']=='READY' for x in reports),'errors':sum(x['status']=='ERROR' for x in reports)}
 (root/'docs'/'import_registry.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');return payload
