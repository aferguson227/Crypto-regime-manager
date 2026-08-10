#!/usr/bin/env python3
"""V66 resident KuCoin Live Trading Data Service.

Runs locally under the same Windows user/credential context as RUN_LOCAL_AGENT.ps1.
It refreshes canonical read-only KuCoin trading truth frequently without invoking
research/backtesting. No order-placement endpoint is implemented.
"""
from __future__ import annotations
import json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs'
OUT=D/'kucoin_live_service_status.json'
LOCK=(Path(os.getenv('LOCALAPPDATA') or str(Path.home()))/'CryptoRegimeManager'/'kucoin_live_service.lock')

FAST=['scripts.kucoin_live_price_engine','scripts.kucoin_order_state','scripts.live_portfolio_truth_engine']
MEDIUM=['scripts.kucoin_account_sync','scripts.kucoin_fill_ledger','scripts.execution_reconciliation_engine',
        'scripts.capital_intelligence_engine','scripts.independent_trade_accounting_engine',
        'scripts.portfolio_capital_manager_v2','scripts.execution_assurance_engine',
        'scripts.kucoin_canonical_service','scripts.integrity_guard_engine']

def now():return datetime.now(timezone.utc).isoformat()
def runmod(m):
 st=time.monotonic()
 r=subprocess.run([sys.executable,'-m',m],cwd=ROOT,text=True,capture_output=True)
 return {'module':m,'status':'OK' if r.returncode==0 else 'DEGRADED','seconds':round(time.monotonic()-st,2),
         'detail':(r.stdout or r.stderr)[-600:]}
def write(status,cycle,rows,last_full=None):
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'status':status,
    'cycle':cycle,'pid':os.getpid(),'fast_interval_seconds':20,'private_refresh_interval_seconds':60,
    'last_full_private_refresh_at':last_full,'modules':rows,'read_only':True,'write_endpoints_implemented':False,
    'principle':'One resident local process owns the frequent KuCoin truth refresh. Research and live execution are separate.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8')
def acquire_lock():
 LOCK.parent.mkdir(parents=True,exist_ok=True)
 if LOCK.exists():
  try:
   old=int(LOCK.read_text().strip())
   if old and old!=os.getpid():
    # Best-effort check; on Windows task scheduler should already enforce one instance.
    return False
  except:pass
 LOCK.write_text(str(os.getpid()),encoding='utf-8');return True
def main():
 if not acquire_lock():
  print('KuCoin Live Data Service: existing instance lock detected; exiting safely.')
  return 0
 cycle=0;last_private=0.0;last_full=None
 try:
  while True:
   cycle+=1;rows=[]
   for m in FAST:rows.append(runmod(m))
   if time.monotonic()-last_private>=60:
    for m in MEDIUM:rows.append(runmod(m))
    last_private=time.monotonic();last_full=now()
   status='HEALTHY' if all(x['status']=='OK' for x in rows) else 'DEGRADED'
   write(status,cycle,rows,last_full)
   time.sleep(20)
 except KeyboardInterrupt:return 0
 finally:
  try:
   if LOCK.exists() and LOCK.read_text().strip()==str(os.getpid()):LOCK.unlink()
  except:pass
if __name__=='__main__':raise SystemExit(main())
