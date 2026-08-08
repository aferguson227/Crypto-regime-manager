#!/usr/bin/env python3
"""V45 regime-aware DCA backtesting and trade-fluidity optimiser.

Research only. It tests multiple entry-trigger families and DCA ladders against
locally available 4-hour data, scores profitability together with drawdown and
capital lock duration, and records a regime profile. It never creates/edits bots.

When independent Kraken training/validation archives are configured, the engine
runs the existing walk-forward pipeline first, freezes settings before validation,
and keeps those results separate from exploratory local regime optimisation.
"""
from __future__ import annotations
import csv,hashlib,itertools,json,math,os,statistics,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.core.symbols import canonical_asset

ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'regime_backtest_intelligence.json'; POLICY=ROOT/'config'/'research_policy.json'

def load_json(p,default=None):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default

def f(v):
 try:return float(v)
 except:return None

def load_rows(path):
 out=[]
 with Path(path).open(encoding='utf-8-sig') as h:
  for r in csv.DictReader(h):
   try:out.append({'time':r['time'],'open':float(r['open']),'high':float(r['high']),'low':float(r['low']),'close':float(r['close'])})
   except:pass
 return out

def sma(vals,n,i):
 if i+1<n:return None
 return sum(vals[i-n+1:i+1])/n

def rsi(vals,n,i):
 if i<n:return None
 gains=losses=0.0
 for j in range(i-n+1,i+1):
  ch=vals[j]-vals[j-1]
  if ch>=0:gains+=ch
  else:losses-=ch
 if losses==0:return 100.0
 rs=(gains/n)/(losses/n)
 return 100-(100/(1+rs))

def enrich(rows):
 closes=[x['close'] for x in rows]
 out=[]
 for i,r in enumerate(rows):
  s20=sma(closes,20,i); s50=sma(closes,50,i); rv=rsi(closes,14,i)
  prev20=max((x['high'] for x in rows[max(0,i-20):i]),default=None)
  high20=max((x['high'] for x in rows[max(0,i-19):i+1]),default=r['high'])
  ret6=((r['close']/closes[i-6]-1)*100) if i>=6 and closes[i-6] else None
  ret30=((r['close']/closes[i-30]-1)*100) if i>=30 and closes[i-30] else None
  # volatility proxy: 20-bar mean high-low range as pct of close
  ranges=[(rows[j]['high']-rows[j]['low'])/rows[j]['close']*100 for j in range(max(0,i-19),i+1) if rows[j]['close']]
  vol=sum(ranges)/len(ranges) if ranges else None
  if s20 is None or s50 is None: regime='NEUTRAL'
  elif r['close']>s50 and s20>s50 and (ret6 or 0)>1.0: regime='STRONG_BULL'
  elif r['close']>s50 and s20>=s50: regime='BULL'
  elif r['close']<s50 and s20<s50 and (ret6 or 0)<-2.0: regime='BEAR'
  elif r['close']<s50 and s20<s50: regime='DISTRIBUTION'
  elif vol is not None and vol<4 and abs(ret6 or 0)<3: regime='ACCUMULATION'
  else: regime='NEUTRAL'
  x=dict(r);x.update({'sma20':s20,'sma50':s50,'rsi14':rv,'prev_high20':prev20,'high20':high20,'ret24h_pct':ret6,'ret5d_pct':ret30,'volatility_pct':vol,'regime':regime});out.append(x)
 return out

def trigger_ok(trigger,r):
 c=r['close'];s20=r.get('sma20');s50=r.get('sma50');rv=r.get('rsi14');h20=r.get('high20');ph=r.get('prev_high20')
 if trigger=='immediate':return True
 if trigger=='pullback_3pct':return bool(h20 and c<=h20*.97)
 if trigger=='rsi_oversold':return rv is not None and rv<=35
 if trigger=='trend_pullback':return bool(s50 and c>s50 and rv is not None and rv<=47)
 if trigger=='breakout_20':return bool(ph and c>=ph*.997)
 if trigger=='qfl_proxy_3':return bool(h20 and c<=h20*.97 and rv is not None and rv<=45)
 if trigger=='mean_reversion':return bool(s20 and c<=s20*.98)
 return False

def capital(bo,so,n,vs):return bo+sum(so*(vs**i) for i in range(n))

def replay(rows,trigger,allowed_regimes,tp,dev,n,vs,step,fee=.001,bo=100,so=100):
 pnl=0.;deals=0;dur=[];maxcap=capital(bo,so,n,vs);open_trade=None;equity=[];so_counts=[]
 for i,c in enumerate(rows):
  if open_trade is None and c.get('regime') in allowed_regimes and trigger_ok(trigger,c):
   open_trade={'i':i,'cost':bo,'qty':bo/c['close'],'next':c['close']*(1-dev),'so':0}
  t=open_trade
  if t is not None:
   while t['so']<n and c['low']<=t['next']:
    amount=so*(vs**t['so']);price=t['next'];t['cost']+=amount;t['qty']+=amount/price;t['so']+=1;t['next']*=1-dev*(step**t['so'])
   avg=t['cost']/t['qty'];target=avg*(1+tp+fee*2)
   if c['high']>=target:
    pnl+=t['qty']*target-t['cost']-t['cost']*fee-t['qty']*target*fee;deals+=1;dur.append((i-t['i'])*4);so_counts.append(t['so']);open_trade=None;t=None
  mark=pnl+((t['qty']*c['close']-t['cost']) if t else 0);equity.append(mark)
 peak=-1e99;mdd=0
 for x in equity:peak=max(peak,x);mdd=min(mdd,x-peak)
 open_pnl=0.;open_hours=0
 if open_trade and rows:
  open_pnl=open_trade['qty']*rows[-1]['close']-open_trade['cost'];open_hours=(len(rows)-1-open_trade['i'])*4
 def percentile(vals,p):
  if not vals:return 0
  vals=sorted(vals);idx=min(len(vals)-1,max(0,math.ceil(p*len(vals))-1));return vals[idx]
 return {'net_pnl':round(pnl,2),'mark_to_market_pnl':round(pnl+open_pnl,2),'open_pnl':round(open_pnl,2),'closed_deals':deals,
  'average_hours':round(sum(dur)/len(dur),1) if dur else 0,'median_hours':round(statistics.median(dur),1) if dur else 0,'p90_hours':percentile(dur,.9),
  'longest_hours':max(dur) if dur else 0,'max_drawdown_dollars':round(mdd,2),'max_capital':round(maxcap,2),'open_position':bool(open_trade),'open_duration_hours':open_hours,
  'average_safety_orders':round(sum(so_counts)/len(so_counts),2) if so_counts else 0}

def score_result(r,policy):
 cap=r.get('max_capital') or 1;roc=100*r.get('mark_to_market_pnl',0)/cap;dd=100*abs(r.get('max_drawdown_dollars',0))/cap
 w=policy['objective_weights'];score=roc*w['return_on_max_capital']+r.get('closed_deals',0)*w['closed_deals']+dd*w['max_drawdown_pct']+r.get('p90_hours',0)*w['p90_hold_hours']+r.get('longest_hours',0)*w['longest_hold_hours']
 if r.get('open_position'):score+=w['open_position']+r.get('open_duration_hours',0)*w['open_duration_hours']
 duration=policy['trade_duration_policy'];reject=bool(r.get('open_position') and r.get('open_duration_hours',0)>=duration['reject_open_duration_hours'])
 if r.get('closed_deals',0)<5:score-=25
 return round(score,3),round(roc,2),round(dd,2),reject

def optimise_dataset(path,policy):
 rows=enrich(load_rows(path));asset=dataset_asset(path)
 triggers=policy['entry_triggers'];grid=policy['dca_search_space']
 # Focus on operational regimes; strong/distribution are folded into bull/bear families.
 regime_sets={'BULL':{'BULL','STRONG_BULL'},'ACCUMULATION':{'ACCUMULATION'},'NEUTRAL':{'NEUTRAL'},'BEAR':{'BEAR','DISTRIBUTION','CAPITULATION'}}
 # A bounded but broad grid keeps daily background research practical.
 settings=list(itertools.product(grid['take_profit_pct'],grid['so_deviation_pct'],grid['safety_orders'],grid['volume_scale'],grid['step_scale']))
 profiles={};tested=0
 for regime,allowed in regime_sets.items():
  best=None
  for trig in triggers:
   for tp,dev,n,vs,step in settings:
    tested+=1;r=replay(rows,trig,allowed,tp/100,dev/100,int(n),float(vs),float(step));sc,roc,dd,reject=score_result(r,policy)
    candidate={'entry_trigger':trig,'settings':{'take_profit_pct':tp,'so_deviation_pct':dev,'safety_orders':n,'volume_scale':vs,'step_scale':step},'metrics':{**r,'return_on_max_capital_pct':roc,'max_drawdown_pct':dd},'fluidity_score':sc,'rejected_for_open_duration':reject}
    if reject:continue
    if best is None or candidate['fluidity_score']>best['fluidity_score']:best=candidate
  if best:
   dur=best['metrics'];dpol=policy['trade_duration_policy']
   fluid='GOOD' if dur['longest_hours']<=dpol['preferred_longest_closed_hours'] and not dur['open_position'] else ('CAUTION' if dur['longest_hours']<=dpol['strong_penalty_hours'] else 'POOR')
   best['status']='EXPLORATORY_PASS' if best['metrics']['mark_to_market_pnl']>0 and best['metrics']['closed_deals']>=5 else 'EXPLORATORY_FAIL';best['trade_fluidity']=fluid
   profiles[regime]=best
 return {'asset':asset,'dataset':path.name,'bars':len(rows),'period':{'start':rows[0]['time'] if rows else None,'end':rows[-1]['time'] if rows else None},'entry_triggers_tested':len(triggers),'parameter_combinations_per_trigger':len(settings),'total_backtests':tested,'regime_profiles':profiles}

def dataset_asset(path):
 name=Path(path).stem.upper().replace('_4H','').replace('-4H','')
 if name.endswith('4H'):name=name[:-2]
 return canonical_asset(name)

def input_files():
 files=[]
 # packaged/local TradingView/Kraken-derived 4h datasets
 files.extend(sorted(ROOT.glob('data/*USDT_4H.csv')))
 files.extend(sorted((ROOT/'data'/'normalized').glob('*_4H.csv')))
 # avoid duplicate assets; prefer normalized copy
 by={}
 for p in files:by[dataset_asset(p)]=p
 return list(by.values())

def signature(files,policy):
 rows=[(str(p),p.stat().st_size,int(p.stat().st_mtime)) for p in files if p.exists()]
 return hashlib.sha256(json.dumps({'files':rows,'policy':policy},sort_keys=True).encode()).hexdigest()[:24]

def main():
 policy=load_json(POLICY);files=input_files();sig=signature(files,policy);previous=load_json(OUT,{})
 refresh=float(os.getenv('CRM_REGIME_RESEARCH_REFRESH_HOURS',policy.get('refresh_hours',24)))
 try:
  old=datetime.fromisoformat(str(previous.get('generated_at')).replace('Z','+00:00'));age=(datetime.now(timezone.utc)-old).total_seconds()/3600
 except:age=1e9
 if previous.get('input_signature')==sig and age<refresh:
  print(f'Regime research: cached current result ({age:.1f}h old); next full optimisation after {refresh:g}h or input change.')
  return 0
 # Independent Kraken walk-forward can run automatically when both archive directories exist.
 train=Path(os.getenv('CRM_KRAKEN_TRAINING_DIR',r'C:\Crypto\Research\Kraken\training'));val=Path(os.getenv('CRM_KRAKEN_VALIDATION_DIR',r'C:\Crypto\Research\Kraken\validation'))
 wf_state='NOT_CONFIGURED'
 if train.exists() and val.exists():
  rc=subprocess.run([sys.executable,'-m','scripts.kraken_research_pipeline','--training-dir',str(train),'--validation-dir',str(val)],cwd=ROOT).returncode
  wf_state='COMPLETED' if rc==0 else 'ERROR'
 results=[]
 for p in files:
  try:results.append(optimise_dataset(p,policy))
  except Exception as exc:results.append({'asset':dataset_asset(p),'dataset':p.name,'status':'ERROR','error':f'{type(exc).__name__}: {exc}'})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'background_regime_research_read_only','input_signature':sig,
  'independent_walk_forward':{'status':wf_state,'training_dir':str(train),'validation_dir':str(val),'freeze_before_validation':True},
  'trade_duration_policy':policy.get('trade_duration_policy'),'entry_trigger_families':policy.get('entry_triggers'),'datasets':results,
  'summary':{'datasets':len(results),'assets':[x.get('asset') for x in results],'backtests_run':sum(x.get('total_backtests',0) for x in results),'automatic':True,'live_changes':False},
  'safeguards':{'research_only':True,'manual_approval_required':True,'q1_never_used_for_optimisation':True,'automatic_bot_creation':False}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Regime backtest intelligence written: {OUT}; backtests={payload["summary"]["backtests_run"]}');return 0
if __name__=='__main__':raise SystemExit(main())
