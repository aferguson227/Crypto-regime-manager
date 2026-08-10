#!/usr/bin/env python3
"""V63 decision/research/accounting/execution integrity guard."""
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'integrity_status.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 cont=load('cross_exchange_continuation.json');fills=load('kucoin_fill_ledger.json');cap=load('portfolio_capital_v2.json');life=load('deployment_lifecycle.json')
 unresolved=[x.get('asset') for x in cont.get('assets') or [] if str(x.get('continuation_status') or '') not in {'CLOSED_ON_KUCOIN_CONTINUATION','RESOLVED','PASS','NOT_REQUIRED'}]
 fs=str(fills.get('realised_profit_status') or 'UNKNOWN')
 research={'status':'GOOD' if not unresolved else 'ATTENTION','unresolved_assets':unresolved,'detail':('All required continuation evidence is resolved.' if not unresolved else f'{len(unresolved)} candidate(s) still have unresolved Kraken → KuCoin continuation evidence.')}
 accounting={'status':'GOOD' if fs in {'COMPLETE','NO_CLOSED_TRADES'} else ('LIMITED' if fs=='HISTORICAL_COST_BASIS_UNAVAILABLE' else 'UPDATING'),'detail':fills.get('progress_explanation') or fs}
 pool=cap.get('safe_multi_bot_pool_usdt')
 execution={'status':'READY' if pool is not None and pool>0 else 'WAITING_FOR_CAPITAL','safe_multi_bot_pool_usdt':pool,'detail':'Safe multi-bot capital is available.' if pool and pool>0 else 'No capital is currently available under the portfolio safety policy.'}
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'research_integrity':research,'accounting_integrity':accounting,'execution_readiness':execution,'system_health_scope':'Application/collector/safety health remains separate from research and accounting limitations.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print('Integrity guard written');return 0
if __name__=='__main__':raise SystemExit(main())
