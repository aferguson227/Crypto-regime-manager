#!/usr/bin/env python3
"""V65 public KuCoin live-price collector for current open-position valuation.

No API credentials are required and no trading endpoint is used.
"""
from __future__ import annotations
import json,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'kucoin_live_prices.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def fetch(symbol):
 url='https://api.kucoin.com/api/v1/market/orderbook/level1?'+urllib.parse.urlencode({'symbol':symbol})
 try:
  with urllib.request.urlopen(url,timeout=12) as r:p=json.loads(r.read().decode('utf-8'))
  d=p.get('data') or {}
  if p.get('code')=='200000' and d.get('price') is not None:
   return {'symbol':symbol,'status':'OK','price':float(d['price']),'exchange_time_ms':d.get('time')}
  return {'symbol':symbol,'status':'ERROR','message':str(p.get('msg') or p.get('code'))}
 except Exception as exc:return {'symbol':symbol,'status':'ERROR','message':f'{type(exc).__name__}: {exc}'}
def main():
 cap=load('capital_intelligence.json');assets=sorted({str(x.get('asset') or '').upper() for x in cap.get('asset_allocations') or [] if x.get('asset')})
 rows=[fetch(f'{a}-USDT') for a in assets]
 now=datetime.now(timezone.utc).isoformat()
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'source':'KuCoin public level-1 ticker',
    'prices':rows,'status':'OK' if rows and all(x['status']=='OK' for x in rows) else ('NO_OPEN_ASSETS' if not rows else 'DEGRADED'),
    'read_only':True,'credentials_required':False,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f"KuCoin live prices: {p['status']}; assets={len(rows)}");return 0
if __name__=='__main__':raise SystemExit(main())
