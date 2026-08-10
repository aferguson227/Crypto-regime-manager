#!/usr/bin/env python3
"""V62 on-demand Kraken Q1 evidence materialisation for continuation analysis.

The historical walk-forward registry preserves the original Q1 metrics, but older
source packages may not contain the normalized Q1 candle file used to reconstruct
an open validation position. This manager locates the user's permanent Kraken Q1
archive/folder, extracts only the unresolved assets, normalizes them to 4-hour
candles in persistent CRM_Data, and leaves the original Kraken pass/fail untouched.

Heavy archive work is intended for the isolated Research Worker, not the 15-minute
operational Local Agent.
"""
from __future__ import annotations
import json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.core.data_import import csv_sources,choose_best_source,import_file
from scripts.core.symbols import symbol_key,canonical_asset

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kraken_validation_evidence_status.json'

def load(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 return Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
def out_dir():
 p=data_root()/'Kraken'/'validation_4h';p.mkdir(parents=True,exist_ok=True);return p
def sources():
 explicit=os.getenv('CRM_KRAKEN_VALIDATION_DIR')
 rows=[]
 for p in [explicit, r'C:\Crypto\Kraken Data\Q1_2026.zip', r'C:\Crypto\Kraken Data\Q1_2026',
           r'C:\Crypto\Research\Kraken\validation', ROOT/'data'/'research'/'validation_4h']:
  if not p:continue
  q=Path(p)
  if q.exists() and q not in rows:rows.append(q)
 return rows
def existing(asset):
 for p in [out_dir()/f'{asset}USD_4H.csv',out_dir()/f'{asset}USDT_4H.csv',
           ROOT/'data'/'research'/'validation_4h'/f'{asset}USD_4H.csv',
           ROOT/'data'/'research'/'validation_4h'/f'{asset}USDT_4H.csv']:
  if p.exists():return p
 return None
def main():
 reg=load(DOCS/'walk_forward_registry.json');needed=[]
 for x in reg.get('coins') or []:
  if (x.get('q1_2026_metrics') or {}).get('open_position'):
   a=canonical_asset(str(x.get('symbol') or '').replace('XBT','BTC'))
   if a and a not in needed:needed.append(a)
 rows=[];srcs=sources()
 for asset in needed:
  ex=existing(asset)
  if ex:
   rows.append({'asset':asset,'status':'READY','file':str(ex),'source':'existing normalized evidence'});continue
  found=None;errors=[]
  for source in srcs:
   try:
    with tempfile.TemporaryDirectory(prefix=f'crm-kraken-{asset.lower()}-') as td:
     files=csv_sources(source,Path(td))
     groups={}
     for f in files:groups.setdefault(canonical_asset(symbol_key(f.name)),[]).append(f)
     choices=groups.get(asset) or []
     if not choices:continue
     best=choose_best_source(choices)
     result=import_file(best,out_dir())
     found=Path(result.output_path)
     rows.append({'asset':asset,'status':'MATERIALISED','file':str(found),'source':str(source),
                  'source_file':best.name,'import':result.as_dict()})
     break
   except Exception as exc:errors.append(f'{source}: {type(exc).__name__}: {exc}')
  if not found:
   rows.append({'asset':asset,'status':'MISSING_SOURCE','file':None,'sources_checked':[str(x) for x in srcs],
                'errors':errors[-5:],
                'explanation':'CRM could not locate comparable Q1 Kraken source data for this asset. Configure CRM_KRAKEN_VALIDATION_DIR or keep Q1_2026.zip at C:\\Crypto\\Kraken Data.'})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
          'persistent_output_dir':str(out_dir()),'source_locations':[str(x) for x in srcs],
          'assets':rows,'summary':{'required':len(needed),'ready':sum(x['status'] in {'READY','MATERIALISED'} for x in rows),
                                   'missing':sum(x['status']=='MISSING_SOURCE' for x in rows)},
          'principle':'Materialise only the evidence needed to reconstruct unresolved Kraken-open validations; never rewrite the original Kraken result.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"Kraken validation evidence: ready={payload['summary']['ready']}/{payload['summary']['required']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
