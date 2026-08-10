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
 persistent=data_root()/'Kraken'/'validation_4h'
 for p in [persistent/f'{asset}USD_4H.csv',persistent/f'{asset}USDT_4H.csv',
           ROOT/'data'/'research'/'validation_4h'/f'{asset}USD_4H.csv',ROOT/'data'/'research'/'validation_4h'/f'{asset}USDT_4H.csv']:
  if p.exists():return p
 return None
def coverage(rows,cutoff):
 if not rows:return {'bars':0,'first':None,'last':None,'post_cutoff_bars':0,'first_post_cutoff':None,'gap_hours':None}
 ordered=sorted(rows,key=lambda x:x['time']);future=[x for x in ordered if x['time']>cutoff]
 first_future=future[0]['time'] if future else None
 return {'bars':len(ordered),'first':ordered[0]['time'].isoformat(),'last':ordered[-1]['time'].isoformat(),
  'post_cutoff_bars':len(future),'first_post_cutoff':first_future.isoformat() if first_future else None,
  'gap_hours':round((first_future-cutoff).total_seconds()/3600,1) if first_future else None}
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
       'kucoin_continuation_file':str(kf),'kucoin_file_exists':kf.exists(),'validation_file':str(vf) if vf else None,
       'kraken_cutoff':(coin.get('validation_import') or {}).get('end')}
  cutoff_raw=(coin.get('validation_import') or {}).get('end')
  if not cutoff_raw:
   rec.update({'continuation_status':'MISSING_KRAKEN_CUTOFF','reason':'The preserved Kraken registry does not contain a validation cutoff timestamp.'});rows.append(rec);continue
  cutoff=datetime.fromisoformat(str(cutoff_raw).replace('Z','+00:00'))
  if not vf:
   rec.update({'continuation_status':'KRAKEN_EVIDENCE_MATERIALISING',
    'reason':'The normalized Q1 Kraken file needed to reconstruct the frozen open position is missing. The isolated Research Worker now materialises it automatically from Q1_2026.zip or the configured Kraken validation directory.'});rows.append(rec);continue
  if not kf.exists():
   rec.update({'continuation_status':'KUCOIN_HISTORY_ACQUIRING','reason':'KuCoin 4-hour continuation history is not cached yet. Historical acquisition is prioritising this asset automatically.'});rows.append(rec);continue
  if not settings:
   rec.update({'continuation_status':'FROZEN_SETTINGS_MISSING','reason':'The original Kraken registry does not contain the frozen DCA settings required to reconstruct the position.'});rows.append(rec);continue

  vr=replay(load(vf),float(settings['take_profit_pct'])/100,float(settings['so_deviation_pct'])/100,int(settings['safety_orders']),float(settings['volume_scale']),float(settings['step_scale']))
  state=vr.get('open_state')
  if not state:
   rec.update({'continuation_status':'REPLAY_DID_NOT_END_OPEN','reason':'Current deterministic replay no longer reconstructs the historical open state; original registry remains authoritative and this discrepancy requires research review.'});rows.append(rec);continue

  kurows=load(kf);cov=coverage(kurows,cutoff);future=[x for x in kurows if x['time']>cutoff]
  rec['kucoin_coverage']=cov
  if not future:
   rec.update({'continuation_status':'KUCOIN_HISTORY_DOES_NOT_REACH_CUTOFF',
    'reason':f"Cached KuCoin history ends at {cov.get('last')}; continuation requires candles after Kraken cutoff {cutoff.isoformat()}. Acquisition remains prioritised."});rows.append(rec);continue
  # A gap of more than two 4-hour bars is reported explicitly instead of silently treating the streams as perfectly contiguous.
  if cov.get('gap_hours') is not None and cov['gap_hours']>8.5:
   rec.update({'continuation_status':'KUCOIN_CONTINUATION_GAP',
    'reason':f"First available KuCoin candle after the Kraken cutoff is {cov['gap_hours']}h later. CRM will not call this directly comparable until the historical gap is filled.",
    'future_bars_available':len(future)});rows.append(rec);continue

  result=continue_position(state,future,settings)
  rec.update({'continuation_status':result.get('status'),'reconstructed_open_state':state,'continuation':result,
              'interpretation':'Continuation evidence describes what happened after the frozen Kraken cutoff. The original Kraken result stays preserved; a resolved KuCoin continuation removes a deployment-data blocker but is not itself a trading signal.'})
  rows.append(rec)
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'method':'Reconstruct frozen Kraken cutoff open position, then continue it using later KuCoin 4h candles only.',
  'assets':rows,'summary':{'open_at_kraken_cutoff':len(rows),'closed_later_on_kucoin':sum(x.get('continuation_status')=='CLOSED_ON_KUCOIN_CONTINUATION' for x in rows),
  'still_open':sum(x.get('continuation_status')=='STILL_OPEN' for x in rows),
  'awaiting_evidence':sum(x.get('continuation_status') in {'KRAKEN_EVIDENCE_MATERIALISING','KUCOIN_HISTORY_ACQUIRING','KUCOIN_HISTORY_DOES_NOT_REACH_CUTOFF','KUCOIN_CONTINUATION_GAP'} for x in rows)}, 'safeguards':{'original_validation_rewritten':False,'research_only':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Cross-exchange continuation written: {OUT}; assets={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
