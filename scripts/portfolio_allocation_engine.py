#!/usr/bin/env python3
"""V51 multi-bot portfolio allocation intelligence. Advisory/read-only."""
from __future__ import annotations
import csv,json,math,os,statistics
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'portfolio_allocation_recommendations.json';POL=ROOT/'config'/'v51_execution_policy.json'
def load(p):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def data_root():
 raw=os.getenv('CRM_DATA_ROOT');return Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
def closes(asset):
 p=data_root()/'KuCoin'/'4h'/f'{asset}-USDT_4H.csv'
 if not p.exists():return []
 try:
  with p.open(encoding='utf-8-sig') as f:return [float(r['close']) for r in csv.DictReader(f)][-500:]
 except:return []
def corr(a,b):
 n=min(len(a),len(b))
 if n<40:return None
 ra=[a[i]/a[i-1]-1 for i in range(len(a)-n+1,len(a))];rb=[b[i]/b[i-1]-1 for i in range(len(b)-n+1,len(b))]
 ma=statistics.mean(ra);mb=statistics.mean(rb);sa=sum((x-ma)**2 for x in ra);sb=sum((x-mb)**2 for x in rb)
 if sa<=0 or sb<=0:return None
 return sum((x-ma)*(y-mb) for x,y in zip(ra,rb))/math.sqrt(sa*sb)
def main():
 cap=load(DOCS/'capital_intelligence.json');cap2=load(DOCS/'portfolio_capital_v2.json');review=load(DOCS/'candidate_review.json');reg=load(DOCS/'coin_registry.json');p=load(POL);policy=p.get('portfolio') or {}
 deploy=num(cap2.get('safe_multi_bot_pool_usdt'));free=num(cap.get('free_available'))
 if deploy is None and free is not None:
  reserve=num(cap.get('remaining_active_deal_dca_reserve')) or num(cap.get('reserved_capital')) or 0;deploy=max(0,free-reserve)
 cash_pct=float(policy.get('cash_buffer_pct',15));usable=max(0,deploy*(1-cash_pct/100)) if deploy is not None else None
 live=[x for x in reg.get('coins') or [] if x.get('lifecycle')=='LIVE_PRODUCTION'];slots=max(0,int(policy.get('max_live_bots',4))-len(live))
 candidates=[x for x in review.get('candidates') or [] if all(g.get('state')=='PASS' for g in (x.get('gates') or []) if g.get('id')!='capital_allocation')]
 live_series={x['asset']:closes(x['asset']) for x in live};scored=[]
 for x in candidates:
  vm=x.get('validation_metrics') or {};maxcap=num(vm.get('max_capital')) or 1;ret=100*(num(vm.get('mark_to_market_pnl')) or 0)/maxcap;dd=100*abs(num(vm.get('max_drawdown_dollars')) or 0)/maxcap;longh=num(vm.get('longest_hours')) or 0
  cs=closes(x['asset']);cors=[abs(corr(cs,v)) for v in live_series.values() if corr(cs,v) is not None];cpen=max(cors) if cors else 0
  lock=min(1,longh/(24*14));base=max(0,ret);score=max(0,base*(1-float(policy.get('drawdown_penalty_weight',.35))*min(1,dd/40)-float(policy.get('capital_lock_penalty_weight',.30))*lock-float(policy.get('correlation_penalty_weight',.35))*cpen))
  scored.append((score,x,ret,dd,longh,cpen))
 scored.sort(key=lambda z:z[0],reverse=True);chosen=scored[:slots] if slots else []
 total=sum(x[0] for x in chosen) or 1;rows=[]
 for score,x,ret,dd,longh,cpen in scored:
  selected=any(y[1].get('asset')==x.get('asset') for y in chosen);amount=None
  if usable is not None and selected:
   weighted=usable*(score/total);cap_pct=usable*float(policy.get('max_single_bot_pct',30))/100;pilot=usable*float(policy.get('pilot_pct',15))/100
   amount=round(min(max(pilot,weighted),cap_pct,usable),2)
  if amount is None and deploy is not None and deploy<=0: amount=0.0
  rows.append({'asset':x.get('asset'),'pair':x.get('pair'),'selected_for_next_portfolio_slot':selected,'portfolio_score':round(score,2),
   'kucoin_validation_return_on_max_capital_pct':round(ret,2),'validation_drawdown_pct':round(dd,2),'longest_validation_trade_hours':longh,
   'max_abs_correlation_to_live_bots':round(cpen,3) if cpen is not None else None,'recommended_allocation_usdt':amount,
   'reason':('Selected within available portfolio slot using return, drawdown, capital-lock and diversification penalties.' if selected else 'Evidence passes deployment review, but current portfolio slots/relative score do not justify immediate allocation.'),
   'manual_approval_required':True})
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'deployable_capital_usdt':deploy,
  'cash_buffer_pct':cash_pct,'usable_after_cash_buffer_usdt':round(usable,2) if usable is not None else None,'current_live_bots':[x['asset'] for x in live],
  'maximum_live_bots':int(policy.get('max_live_bots',4)),'available_new_bot_slots':slots,'recommendations':rows,'automatic_deployment':False,
  'capital_source':'Portfolio Capital Manager 2.0 prudent multi-bot pool','allocation_status':'KNOWN' if deploy is not None else 'WAITING_FOR_CAPITAL_TRUTH'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Portfolio allocation written: {OUT}; live={len(live)} slots={slots} candidates={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
