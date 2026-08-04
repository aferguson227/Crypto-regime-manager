from __future__ import annotations
import csv, json, math, re, shutil, tempfile, zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

ALIASES={
 'time':['time','timestamp','date','datetime','open_time','unix','epoch'],
 'open':['open','o'],'high':['high','h'],'low':['low','l'],'close':['close','c'],
 'volume':['volume','vol','v','base_volume'],'trades':['trades','count','trade_count'],
 'price':['price'],'trade_id':['trade_id','trade id','id']}
OHLC_HEADER=['time','open','high','low','close','volume','trades']

@dataclass
class ImportResult:
 exchange:str; symbol:str; source_kind:str; source_timeframe_minutes:int; target_timeframe_minutes:int
 rows_in:int; rows_out:int; dropped_rows:int; duplicate_rows:int; missing_source_intervals:int
 start:str|None; end:str|None; output_path:str|None=None; warnings:list[str]|None=None
 def as_dict(self): return self.__dict__.copy()

def _norm(s:str)->str:return re.sub(r'[^a-z0-9]+','_',str(s).strip().lower()).strip('_')
def _map(headers:Iterable[str])->dict[str,str]:
 n={_norm(h):h for h in headers}; out={}
 for key,vals in ALIASES.items():
  for v in vals:
   if _norm(v) in n: out[key]=n[_norm(v)]; break
 return out

def _time(v:Any)->datetime:
 s=str(v).strip()
 if re.fullmatch(r'\d+(\.\d+)?',s):
  x=float(s)
  if x>1e15:x/=1e9
  elif x>1e12:x/=1e3
  elif x<100000:return datetime.fromtimestamp((x-25569)*86400,tz=timezone.utc)
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
 if 'kraken' in text or {'price','volume','timestamp','type'}.issubset({_norm(x) for x in headers}):return 'Kraken'
 if 'kucoin' in text:return 'KuCoin'
 if 'binance' in text or 'open_time' in text:return 'Binance'
 if 'coinbase' in text:return 'Coinbase'
 if 'tradingview' in text:return 'TradingView'
 return 'Generic OHLCV'

def identify_symbol(filename:str,rows:list[dict[str,Any]]|None=None)->str:
 rows=rows or []
 for k in ('symbol','pair','ticker'):
  if rows and k in {_norm(x):x for x in rows[0]}:
   original={_norm(x):x for x in rows[0]}[k]; val=str(rows[0].get(original,'')).strip()
   if val:return val.upper().replace('/','-')
 m=re.search(r'([A-Z0-9]{2,12})[-_]?((?:USD|USDT|USDC|EUR|GBP))',Path(filename).stem.upper())
 return f'{m.group(1)}-{m.group(2)}' if m else Path(filename).stem.upper()

def _peek(path:Path,n:int=3)->list[list[str]]:
 with path.open(newline='',encoding='utf-8-sig',errors='replace') as f:
  r=csv.reader(f); return [row for _,row in zip(range(n),r)]

def detect_schema(path:Path)->str:
 rows=_peek(path,3)
 if not rows: raise ValueError('Empty CSV')
 first=[_norm(x) for x in rows[0]]
 if {'price','volume','timestamp','type'}.issubset(set(first)):return 'kraken_trades'
 if {'time','open','high','low','close'}.issubset(set(first)) or {'timestamp','open','high','low','close'}.issubset(set(first)):return 'ohlcv_header'
 # Kraken/TradingView 7-column headerless OHLCV: epoch, O,H,L,C,V,count
 if len(rows[0])>=7:
  try:
   _time(rows[0][0]); nums=list(map(float,rows[0][1:6]))
   if all(math.isfinite(x) and x>0 for x in nums[:4]):return 'ohlcv_headerless'
  except Exception:pass
 raise ValueError('Unsupported CSV schema: expected OHLCV candles or Kraken trade history')

def _load_ohlcv(path:Path,headerless:bool=False)->tuple[list[dict[str,Any]],int,int]:
 raw=[]; dropped=0
 with path.open(newline='',encoding='utf-8-sig',errors='replace') as f:
  if headerless:
   reader=csv.reader(f)
   for row in reader:
    if len(row)<5: dropped+=1; continue
    raw.append(dict(zip(OHLC_HEADER,row[:7]+['0']*(7-len(row)))))
   m={x:x for x in OHLC_HEADER}
  else:
   reader=csv.DictReader(f); m=_map(reader.fieldnames or []); raw=list(reader)
 required={'time','open','high','low','close'}
 if not required.issubset(m): raise ValueError(f'Missing OHLCV columns: {sorted(required-set(m))}')
 out=[]
 for r in raw:
  try:
   d={'time':_time(r[m['time']]),'open':float(r[m['open']]),'high':float(r[m['high']]),'low':float(r[m['low']]),'close':float(r[m['close']]),'volume':float(r.get(m.get('volume',''),0) or 0),'trades':int(float(r.get(m.get('trades',''),0) or 0))}
   if min(d['open'],d['high'],d['low'],d['close'])<=0 or d['high']<d['low']: dropped+=1; continue
   out.append(d)
  except Exception:dropped+=1
 before=len(out); unique={x['time']:x for x in out}; duplicates=before-len(unique)
 return sorted(unique.values(),key=lambda x:x['time']),dropped,duplicates

def _load_kraken_trades(path:Path)->tuple[list[dict[str,Any]],int,int]:
 trades=[]; dropped=0; seen=set(); duplicates=0
 with path.open(newline='',encoding='utf-8-sig',errors='replace') as f:
  reader=csv.reader(f); header=next(reader,None)
  if not header: return [],0,0
  # Kraken exports in this dataset have 6 labels but 7 row values:
  # price, volume, timestamp, side, order type, misc(blank), trade id
  for row in reader:
   try:
    if len(row)<3: dropped+=1; continue
    price=float(row[0]); volume=float(row[1]); when=_time(row[2])
    trade_id=row[-1].strip() if len(row)>=7 else ''
    key=trade_id or (when.timestamp(),price,volume)
    if key in seen: duplicates+=1; continue
    seen.add(key)
    if price<=0 or volume<0: dropped+=1; continue
    trades.append({'time':when,'price':price,'volume':volume})
   except Exception:dropped+=1
 return sorted(trades,key=lambda x:x['time']),dropped,duplicates

def _aggregate_trades(trades:list[dict[str,Any]],minutes:int=240)->list[dict[str,Any]]:
 buckets={}; seconds=minutes*60
 for t in trades:
  key=int(t['time'].timestamp())//seconds*seconds
  buckets.setdefault(key,[]).append(t)
 out=[]
 for key,grp in sorted(buckets.items()):
  grp.sort(key=lambda x:x['time']); prices=[x['price'] for x in grp]
  out.append({'time':datetime.fromtimestamp(key,tz=timezone.utc),'open':prices[0],'high':max(prices),'low':min(prices),'close':prices[-1],'volume':sum(x['volume'] for x in grp),'trades':len(grp)})
 return out

def timeframe_minutes(rows:list[dict[str,Any]])->int:
 diffs=[(b['time']-a['time']).total_seconds()/60 for a,b in zip(rows,rows[1:]) if b['time']>a['time']]
 return max(1,int(round(median(diffs)))) if diffs else 0

def resample(rows:list[dict[str,Any]],minutes:int=240)->list[dict[str,Any]]:
 buckets={}; seconds=minutes*60
 for r in rows:
  key=int(r['time'].timestamp())//seconds*seconds; buckets.setdefault(key,[]).append(r)
 out=[]
 for key,grp in sorted(buckets.items()):
  grp.sort(key=lambda x:x['time']); out.append({'time':datetime.fromtimestamp(key,tz=timezone.utc),'open':grp[0]['open'],'high':max(x['high'] for x in grp),'low':min(x['low'] for x in grp),'close':grp[-1]['close'],'volume':sum(x['volume'] for x in grp),'trades':sum(x['trades'] for x in grp)})
 return out

def _write_candles(dest:Path,rows:list[dict[str,Any]])->None:
 dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(OHLC_HEADER)
  for x in rows:w.writerow([x['time'].isoformat().replace('+00:00','Z'),x['open'],x['high'],x['low'],x['close'],x['volume'],x['trades']])

def import_file(path:Path,out_dir:Path,target_minutes:int=240)->ImportResult:
 schema=detect_schema(path); warnings=[]
 if schema=='kraken_trades':
  trades,dropped,duplicates=_load_kraken_trades(path); rows=_aggregate_trades(trades,target_minutes); src=0; source_kind='trades'
  raw_count=len(trades)+dropped+duplicates
  if not rows: raise ValueError('No valid Kraken trades found')
 else:
  rows,dropped,duplicates=_load_ohlcv(path,schema=='ohlcv_headerless'); src=timeframe_minutes(rows); source_kind='candles'; raw_count=len(rows)+dropped+duplicates
  if src<=0:raise ValueError('Could not determine timeframe')
  if src>target_minutes or target_minutes%src:raise ValueError(f'{src}m data cannot be safely converted to {target_minutes}m')
  if src!=target_minutes: rows=resample(rows,target_minutes)
 symbol=identify_symbol(path.name)
 dest=out_dir/f'{symbol.replace("-","")}_{target_minutes//60}H.csv'; _write_candles(dest,rows)
 expected=(src or target_minutes)*60
 gaps=sum(1 for a,b in zip(rows,rows[1:]) if (b['time']-a['time']).total_seconds()>target_minutes*60*1.5)
 if gaps:warnings.append(f'{gaps} missing 4h intervals detected; gaps are not forward-filled')
 return ImportResult(identify_exchange(_peek(path,1)[0],path.name),symbol,source_kind,src,target_minutes,raw_count,len(rows),dropped,duplicates,gaps,rows[0]['time'].isoformat(),rows[-1]['time'].isoformat(),str(dest),warnings)


def _safe_extract_zip(archive:Path,destination:Path)->list[Path]:
 destination.mkdir(parents=True,exist_ok=True)
 files=[]
 with zipfile.ZipFile(archive) as z:
  for info in z.infolist():
   if info.is_dir() or not info.filename.lower().endswith('.csv'): continue
   target=(destination/info.filename).resolve()
   if destination.resolve() not in target.parents: raise ValueError(f'Unsafe ZIP path: {info.filename}')
   target.parent.mkdir(parents=True,exist_ok=True)
   with z.open(info) as src,target.open('wb') as dst: shutil.copyfileobj(src,dst)
   files.append(target)
 return files

def csv_sources(source:Path,workspace:Path)->list[Path]:
 source=Path(source)
 if source.is_dir():
  files=sorted(source.rglob('*.csv'))
  for archive in sorted(source.rglob('*.zip')):
   files.extend(_safe_extract_zip(archive,workspace/archive.stem))
  return files
 if source.suffix.lower()=='.zip': return _safe_extract_zip(source,workspace/source.stem)
 if source.suffix.lower()=='.csv': return [source]
 raise ValueError(f'Expected a CSV, ZIP or folder: {source}')

def run_import_queue(root:Path)->dict[str,Any]:
 inbox=root/'data'/'imports'; output=root/'data'/'normalized'; reports=[]
 if inbox.exists():
  with tempfile.TemporaryDirectory(prefix='crm_import_') as td:
   try: sources=csv_sources(inbox,Path(td))
   except Exception as e: sources=[]; reports.append({'status':'ERROR','source_file':str(inbox),'error':str(e)})
   for p in sources:
    try: reports.append({'status':'READY',**import_file(p,output).as_dict(),'source_file':p.name})
    except Exception as e: reports.append({'status':'ERROR','source_file':p.name,'error':str(e)})
 payload={'version':'30.1.0','generated_at':datetime.now(timezone.utc).isoformat(),'target_timeframe':'4h','files':reports,'ready':sum(x['status']=='READY' for x in reports),'errors':sum(x['status']=='ERROR' for x in reports)}
 (root/'docs'/'import_registry.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');return payload
