#!/usr/bin/env python3
"""V46 independent read-only portfolio accounting layer.
Uses fresh local KuCoin capital as capital truth and 3Commas deals only as execution telemetry until direct order/fill reconciliation is available.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'independent_trade_accounting.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v)
 except:return 0.0
def main():
 ku=load('kucoin_account.json'); ti=load('trade_intelligence.json'); tc=load('threecommas.json'); ledger=load('kucoin_fill_ledger.json')
 trades=ti.get('trades') or []
 known_open=[x.get('profit_quote') for x in trades if x.get('profit_quote') is not None]
 open_pnl=sum(num(x) for x in known_open) if known_open else None
 deployed=sum(num(x.get('capital_used_quote')) for x in trades)
 # realised fields vary by 3Commas response; publish unknown rather than fabricate.
 realised=ledger.get('realised_profit_quote') if ledger.get('realised_profit_quote') is not None else tc.get('realised_profit_usdt')
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'capital_source':'local KuCoin private read-only account snapshot','execution_telemetry_source':'3Commas until direct KuCoin fill ledger is enabled','active_trade_count':len(trades),'deployed_quote':round(deployed,4),'open_pnl_quote':round(open_pnl,4) if open_pnl is not None else None,'open_pnl_status':'KNOWN' if open_pnl is not None else 'WAITING_FOR_CURRENT_PRICE_OR_ENTRY','realised_profit_quote':realised,'realised_profit_status':'KNOWN' if realised is not None else str(ledger.get('realised_profit_status') or 'BUILDING_KUCOIN_FILL_COST_BASIS'),'realised_profit_source':'KuCoin persistent fill ledger' if ledger.get('realised_profit_quote') is not None else ('3Commas fallback' if tc.get('realised_profit_usdt') is not None else 'KuCoin persistent fill ledger building'),'portfolio_value_quote':ku.get('total_usdt_equivalent') or ku.get('total_equity_usdt'),'read_only':True,'execution_enabled':False,'reconciliation_status':'PARTIAL' if trades else 'CAPITAL_ONLY','migration_note':'V50 persists recent KuCoin spot fills locally so closed-fill cost basis grows across refreshes and upgrades. Realised P/L is published only when the ledger can match the relevant sell fills to known cost basis.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8'); print('Independent trade accounting written:',OUT);return 0
if __name__=='__main__':raise SystemExit(main())
