#!/usr/bin/env python3
"""V51 cross-exchange continuation evidence.

When frozen Kraken Q1 validation ends open, recreate that unresolved position from
the original Q1 validation dataset, then continue only that position through later
KuCoin 4h candles. The original Kraken pass/fail result is never changed.
"""
from __future__ import annotations
import csv,json,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.core.backtest_lab import load,replay
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'cross_exchange_continuation.json'
def now():return datetime.now(timezone.utc).isoformat()
def j(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 if raw:return Path(raw)
 return Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data'
def kucoin_file(asset):return data_root()/'KuCoin'/'4h'/f'{asset}-USDT_4H.csv'
def validation_file(asset):
 for p in [ROOT/'data'/'research'/'validation_4h'/f'{asset}USD_4H.csv',ROOT/'data'/'research'/'validation_4h'/f'{asset}USDT_4H.csv']:
  if p.exists():return p
 return None
def continue_position(state,rows,settings,fee=.001):
 if not state:return {'status':'UNRECONSTRUCTABLE'}
 cost=float(state['cost']);qty=float(state['qty']);nextp=float(state['next_safety_price']);used=int(state['safety_orders_used'])
 n=int(settings['safety_orders']);dev=float(settings['so_deviation_pct'])/100;vs=float(settings['volume_scale']);step=float(settings['step_scale']);tp=float(settings['take_profit_pct'])/100
 entry=datetime.fromisoformat(str(state['entry_time']).replace('Z','+00:00'));min_pnl=1e99;min_price=None
 for row in rows:
  while used<n and row['low']<=nextp:
   amount=100*(vs**used);cost+=amount;qty+=amount/nextp;used+=1;nextp*=1-dev*(step**used)
  avg=cost/qty;target=avg*(1+tp+fee*2);mark=qty*row['close']-cost
  if mark<min_pnl:min_pnl=mark;min_price=row['close']
  if row['high']>=target:
   gross=qty*target-cost;net=gross-cost*fee-qty*target*fee
   return {'status':'CLOSED_ON_KUCOIN_CONTINUATION','closed_at':row['time'].isoformat(),'total_duration_hours':round((row['time']-entry).total_seconds()/3600,1),
    'final_net_pnl':round(net,2),'maximum_adverse_pnl':round(min_pnl,2),'average_entry_at_close':avg,'target_price':target,'safety_orders_used':used}
 last=rows[-1] if rows else None
 return {'status':'STILL_OPEN' if last else 'NO_KUCOIN_CONTINUATION_DATA','latest_at':last['time'].isoformat() if last else None,
  'total_duration_hours':round((last['time']-entry).total_seconds()/3600,1) if last else None,'current_mark_to_market_pnl':round(qty*last['close']-cost,2) if last else None,
  'maximum_adverse_pnl':round(min_pnl,2) if min_pnl<1e98 else None,'safety_orders_used':used}
def main():
 reg=j(DOCS/'walk_forward_registry.json');rows=[]
 for coin in reg.get('coins') or []:
  q=coin.get('q1_2026_metrics') or {}
  if not q.get('open_position'):continue
  asset=str(coin.get('symbol') or '').replace('XBT','BTC').upper();vf=validation_file(asset);kf=kucoin_file(asset);settings=coin.get('frozen_settings') or {}
  rec={'asset':asset,'kraken_cutoff_status':coin.get('status'),'kraken_cutoff_mark_to_market_pnl':q.get('mark_to_market_pnl'),'original_validation_preserved':True,
       'kucoin_continuation_file':str(kf),'validation_file':str(vf) if vf else None}
  if not vf or not kf.exists() or not settings:
   rec.update({'continuation_status':'WAITING_FOR_COMPARABLE_DATA','reason':'Normalized Q1 validation data or later KuCoin 4h history is not available yet.'});rows.append(rec);continue
  vr=replay(load(vf),float(settings['take_profit_pct'])/100,float(settings['so_deviation_pct'])/100,int(settings['safety_orders']),float(settings['volume_scale']),float(settings['step_scale']))
  state=vr.get('open_state')
  if not state:
   rec.update({'continuation_status':'REPLAY_DID_NOT_END_OPEN','reason':'Current deterministic replay no longer reconstructs the historical open state; original registry remains authoritative.'});rows.append(rec);continue
  cutoff=datetime.fromisoformat(str((coin.get('validation_import') or {}).get('end')).replace('Z','+00:00'))
  future=[x for x in load(kf) if x['time']>cutoff]
  result=continue_position(state,future,settings)
  rec.update({'continuation_status':result.get('status'),'reconstructed_open_state':state,'continuation':result,
              'interpretation':'Continuation evidence describes what happened after the frozen Kraken cutoff. It never upgrades the original Kraken validation to PASS.'})
  rows.append(rec)
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'method':'Reconstruct frozen Kraken cutoff open position, then continue it using later KuCoin 4h candles only.',
  'assets':rows,'summary':{'open_at_kraken_cutoff':len(rows),'closed_later_on_kucoin':sum(x.get('continuation_status')=='CLOSED_ON_KUCOIN_CONTINUATION' for x in rows),
  'still_open':sum(x.get('continuation_status')=='STILL_OPEN' for x in rows)},'safeguards':{'original_validation_rewritten':False,'research_only':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Cross-exchange continuation written: {OUT}; assets={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
