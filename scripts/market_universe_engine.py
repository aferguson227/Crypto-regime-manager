#!/usr/bin/env python3
"""V46 two-tier market universe: production USDT research plus experimental BTC pairs."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'market_universe_status.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 src=load('coin_universe.json'); rows=src.get('candidates') or []
 usdt=[x for x in rows if str(x.get('quote_currency') or x.get('quoteCurrency') or '').upper()=='USDT']
 btc=[x for x in rows if str(x.get('quote_currency') or x.get('quoteCurrency') or '').upper()=='BTC']
 eligible=lambda xs:[x for x in xs if x.get('eligible') is True]
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'production_research':{'quote':'USDT','symbols_seen':len(usdt),'eligible':len(eligible(usdt)),'execution_allowed':False},'experimental_research':{'quote':'BTC','symbols_seen':len(btc),'eligible':len(eligible(btc)),'execution_allowed':False,'note':'BTC-quoted markets are research-only until BTC-denominated accounting and validation gates are approved.'},'policy':'scan broadly, backtest selectively, validate rigorously','manual_approval_required':True}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8'); print('Market universe status written:',OUT); return 0
if __name__=='__main__':raise SystemExit(main())
