from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv
from scripts.core.data_import import import_file
from scripts.core.backtest_lab import optimise

def test_v29_import_resamples_hourly_to_4h(tmp_path:Path):
 p=tmp_path/'Kraken_XMRUSD_1h.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume'])
  for i in range(12):w.writerow([1704067200+i*3600,100+i,102+i,99+i,101+i,10])
 r=import_file(p,tmp_path/'out')
 assert r.exchange=='Kraken' and r.source_timeframe_minutes==60 and r.rows_out==3
 assert Path(r.output_path).exists()

def test_v29_backtest_generalised(tmp_path:Path):
 p=tmp_path/'XMRUSD_4H.csv'
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['time','open','high','low','close','volume','trades'])
  for i in range(220):
   price=100+(i%12)*.5
   w.writerow([(datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(hours=4*i)).isoformat().replace('+00:00','Z'),price,price*1.03,price*.98,price*1.01,10,1])
 assert optimise(p)
