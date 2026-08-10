#!/usr/bin/env python3
"""V67 resident KuCoin Live Trading Data Service.

Owns frequent read-only KuCoin operational truth under one Windows user/credential
context. Heavy research/backtesting is deliberately excluded.
"""
from __future__ import annotations
import json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.runtime_state_manager import import_state,capture

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'kucoin_live_service_status.json'
STATE_DIR=(Path(os.getenv('LOCALAPPDATA') or str(Path.home()))/'CryptoRegimeManager')
LOCK=STATE_DIR/'kucoin_live_service.lock'
LOG=STATE_DIR/'kucoin_live_service.log'

FAST=['scripts.kucoin_live_price_engine','scripts.kucoin_order_state','scripts.live_portfolio_truth_engine',
      'scripts.paper_trading_engine','scripts.managed_bot_portfolio_engine']
MEDIUM=['scripts.kucoin_account_sync','scripts.kucoin_fill_ledger','scripts.execution_reconciliation_engine',
        'scripts.capital_intelligence_engine','scripts.independent_trade_accounting_engine',
        'scripts.portfolio_capital_manager_v2','scripts.execution_assurance_engine',
        'scripts.kucoin_canonical_service','scripts.integrity_guard_engine']

def now():return datetime.now(timezone.utc).isoformat()
def log(msg):
 STATE_DIR.mkdir(parents=True,exist_ok=True)
 line=f'{now()} {msg}\n'
 try:
  with LOG.open('a',encoding='utf-8') as f:f.write(line)
  # Keep diagnostics bounded.
  if LOG.stat().st_size>500_000:
   rows=LOG.read_text(encoding='utf-8',errors='ignore').splitlines()[-1200:]
   LOG.write_text('\n'.join(rows)+'\n',encoding='utf-8')
 except:pass
def pid_alive(pid):
 if not pid or pid==os.getpid():return bool(pid)
 try:
  if os.name=='nt':
   r=subprocess.run(['tasklist.exe','/FI',f'PID eq {int(pid)}','/FO','CSV','/NH'],text=True,capture_output=True,timeout=8)
   return r.returncode==0 and str(int(pid)) in r.stdout and 'No tasks are running' not in r.stdout
  os.kill(int(pid),0);return True
 except:return False
def acquire_lock():
 STATE_DIR.mkdir(parents=True,exist_ok=True)
 if LOCK.exists():
  try:old=int(LOCK.read_text().strip() or 0)
  except:old=0
  if old and old!=os.getpid() and pid_alive(old):
   log(f'existing live service pid={old}; new pid={os.getpid()} exits safely');return False
  # Stale lock is self-healed.
  try:LOCK.unlink()
  except:pass
 LOCK.write_text(str(os.getpid()),encoding='utf-8');return True
def write(status,cycle,rows,last_full=None,current_module=None,message=None):
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now(),'heartbeat_at':now(),
  'status':status,'cycle':cycle,'pid':os.getpid(),'fast_interval_seconds':20,'private_refresh_interval_seconds':60,
  'last_full_private_refresh_at':last_full,'current_module':current_module,'message':message,'modules':rows,
  'startup_mechanism':'HKCU per-user startup','read_only':True,'write_endpoints_implemented':False,
  'log_path':str(LOG),'principle':'One resident process owns frequent KuCoin operational truth; research remains isolated.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
def runmod(m,timeout=50):
 st=time.monotonic()
 try:
  r=subprocess.run([sys.executable,'-m',m],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
  return {'module':m,'status':'OK' if r.returncode==0 else 'DEGRADED','seconds':round(time.monotonic()-st,2),
          'detail':(r.stdout or r.stderr)[-800:]}
 except subprocess.TimeoutExpired:
  return {'module':m,'status':'TIMEOUT','seconds':round(time.monotonic()-st,2),'detail':f'Module exceeded {timeout}s and was terminated so the live service can continue.'}
 except Exception as exc:
  return {'module':m,'status':'ERROR','seconds':round(time.monotonic()-st,2),'detail':f'{type(exc).__name__}: {exc}'}
def main():
 if not acquire_lock():
  return 0
 cycle=0;last_private=0.0;last_full=None
 log(f'service started pid={os.getpid()}')
 write('STARTING',cycle,[],last_full,message='Resident KuCoin service started; first live snapshot is being built.')
 try:
  while True:
   cycle+=1;rows=[]
   # Resident service operates only in the isolated Runtime App. Pull the latest
   # authoritative State before calculation and push results back after the cycle.
   import_state(ROOT)
   for m in FAST:
    write('REFRESHING',cycle,rows,last_full,current_module=m)
    result=runmod(m);rows.append(result);log(f'cycle={cycle} {m} {result["status"]} {result["seconds"]}s')
   if time.monotonic()-last_private>=60:
    for m in MEDIUM:
     write('REFRESHING',cycle,rows,last_full,current_module=m)
     result=runmod(m);rows.append(result);log(f'cycle={cycle} {m} {result["status"]} {result["seconds"]}s')
    last_private=time.monotonic();last_full=now()
   status='HEALTHY' if all(x['status']=='OK' for x in rows) else 'DEGRADED'
   write(status,cycle,rows,last_full,message='Live trading truth refreshed.')
   capture(ROOT)
   time.sleep(20)
 except KeyboardInterrupt:
  log('service stopped by KeyboardInterrupt');return 0
 except Exception as exc:
  log(f'uncaught {type(exc).__name__}: {exc}')
  write('ERROR',cycle,[],last_full,message=f'{type(exc).__name__}: {exc}')
  return 1
 finally:
  try:
   if LOCK.exists() and LOCK.read_text().strip()==str(os.getpid()):LOCK.unlink()
  except:pass
if __name__=='__main__':raise SystemExit(main())
