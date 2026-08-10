#!/usr/bin/env python3
"""V63 fast operational truth aggregator.

Designed for the frequent Local Agent loop. It deliberately excludes backtests,
walk-forward and research downloads.
"""
import json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'fast_live_truth_status.json'
MODULES=['scripts.kucoin_account_sync','scripts.kucoin_live_price_engine','scripts.kucoin_fill_ledger','scripts.kucoin_order_state','scripts.execution_reconciliation_engine','scripts.capital_intelligence_engine','scripts.trade_intelligence_engine','scripts.independent_trade_accounting_engine','scripts.live_portfolio_truth_engine','scripts.portfolio_capital_manager_v2','scripts.live_strategy_revalidation_engine','scripts.integrity_guard_engine']
def main():
 rows=[];start=time.monotonic()
 for m in MODULES:
  st=time.monotonic();r=subprocess.run([sys.executable,'-m',m],cwd=ROOT,capture_output=True,text=True)
  rows.append({'module':m,'status':'OK' if r.returncode==0 else 'DEGRADED','seconds':round(time.monotonic()-st,2),'detail':(r.stdout or r.stderr)[-500:]})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'status':'HEALTHY' if all(x['status']=='OK' for x in rows) else 'DEGRADED','seconds':round(time.monotonic()-start,2),'modules':rows,'research_excluded':True,'target_refresh_seconds':60}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f"Fast live truth: {p['status']} in {p['seconds']}s");return 0
if __name__=='__main__':raise SystemExit(main())
