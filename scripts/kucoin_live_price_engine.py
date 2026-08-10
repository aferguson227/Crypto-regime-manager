#!/usr/bin/env python3
"""V67 public KuCoin live-price collector.

One all-tickers request supplies current prices for live positions and paper-managed
deployment candidates. No API credentials or trading endpoint is used.
"""
from __future__ import annotations
import json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'kucoin_live_prices.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def target_assets():
 cap=load('capital_intelligence.json');spec=load('dca_deployment_specs.json');life=load('deployment_lifecycle.json')
 a={str(x.get('asset') or '').upper() for x in cap.get('asset_allocations') or [] if x.get('asset')}
 a|={str(x.get('asset') or '').upper() for x in spec.get('specs') or [] if x.get('recommended_settings_available')}
 a|={str(x.get('asset') or '').upper() for x in life.get('bots') or [] if x.get('asset') and x.get('lifecycle_state') in {'ACTIVE','READY_TO_DEPLOY','READY_FOR_DEPLOYMENT_REVIEW'}}
 return sorted(x for x in a if x)
def main():
 assets=target_assets();rows=[];message=None
 try:
  with urllib.request.urlopen('https://api.kucoin.com/api/v1/market/allTickers',timeout=15) as r:p=json.loads(r.read().decode('utf-8'))
  by={str(x.get('symbol') or '').upper():x for x in ((p.get('data') or {}).get('ticker') or [])}
  for a in assets:
   x=by.get(f'{a}-USDT')
   if x and x.get('last') is not None:rows.append({'symbol':f'{a}-USDT','status':'OK','price':float(x['last']),'change_rate':x.get('changeRate'),'volume':x.get('volValue')})
   else:rows.append({'symbol':f'{a}-USDT','status':'MISSING','message':'Pair not returned by KuCoin all-tickers snapshot.'})
 except Exception as exc:
  message=f'{type(exc).__name__}: {exc}';rows=[{'symbol':f'{a}-USDT','status':'ERROR','message':message} for a in assets]
 now=datetime.now(timezone.utc).isoformat()
 status='OK' if rows and all(x['status']=='OK' for x in rows) else ('NO_TARGET_ASSETS' if not rows else 'DEGRADED')
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now,'source':'KuCoin public all-tickers snapshot',
  'target_assets':assets,'prices':rows,'status':status,'message':message,'read_only':True,'credentials_required':False,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f"KuCoin live prices: {status}; assets={len(rows)}");return 0
if __name__=='__main__':raise SystemExit(main())
