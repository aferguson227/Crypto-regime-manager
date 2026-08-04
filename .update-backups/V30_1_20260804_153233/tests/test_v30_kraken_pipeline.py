from pathlib import Path
import csv
from scripts.core.data_import import import_file, detect_schema

def test_headerless_4h_import(tmp_path:Path):
 p=tmp_path/'XMRUSDT_240.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f)
  for i in range(3):w.writerow([1704067200+i*14400,100+i,102+i,99+i,101+i,10,3])
 assert detect_schema(p)=='ohlcv_headerless'
 r=import_file(p,tmp_path/'out')
 assert r.source_kind=='candles' and r.source_timeframe_minutes==240 and r.rows_out==3

def test_kraken_trade_import_handles_extra_blank_field(tmp_path:Path):
 p=tmp_path/'XMRUSDT.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['Price','Volume','Timestamp','Type','Miscellaneous','Trade ID'])
  w.writerow([100,1,1767225601.0,'b','l','',1]);w.writerow([101,2,1767229201.0,'s','m','',2])
 assert detect_schema(p)=='kraken_trades'
 r=import_file(p,tmp_path/'out')
 assert r.source_kind=='trades' and r.rows_out==1 and r.rows_in==2
