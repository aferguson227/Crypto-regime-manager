#!/usr/bin/env python3
"""V47 KuCoin-primary frozen walk-forward validation for dynamically cached histories."""
from __future__ import annotations
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.regime_backtest_engine import load_rows,enrich,replay,score_result,dataset_asset
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kucoin_walk_forward.json'
POLICY=ROOT/'config'/'kucoin_research_policy.json';RESEARCH=ROOT/'config'/'research_policy.json'
def load(p,default=None):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_dir():
 raw=os.getenv('CRM_DATA_ROOT');base=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 return base/'KuCoin'/'4h'
def family(reg):return 'BULL' if reg in {'BULL','STRONG_BULL'} else ('BEAR' if reg in {'BEAR','DISTRIBUTION','CAPITULATION'} else reg)
def evaluate(rows,profile,allowed,policy):
 if not profile:return None
 st=profile['settings'];r=replay(rows,profile['entry_trigger'],allowed,float(st['take_profit_pct'])/100,float(st['so_deviation_pct'])/100,int(st['safety_orders']),float(st['volume_scale']),float(st['step_scale']))
 sc,roc,dd,reject=score_result(r,policy)
 return {**r,'return_on_max_capital_pct':roc,'max_drawdown_pct':dd,'score':sc,'rejected_for_open_duration':reject}
def train_best(rows,allowed,policy,extensions=None):
 import itertools
 extensions=extensions or {};g=policy['dca_search_space']
 triggers=list(dict.fromkeys(list(policy['entry_triggers'])+list(extensions.get('entry_triggers') or [])))
 def merged(k):return list(dict.fromkeys(list(g[k])+list(extensions.get(k) or [])))
 best=None;tested=0
 for trig in triggers:
  for tp,dev,n,vs,step in itertools.product(merged('take_profit_pct'),merged('so_deviation_pct'),merged('safety_orders'),merged('volume_scale'),merged('step_scale')):
   tested+=1;r=replay(rows,trig,allowed,tp/100,dev/100,int(n),float(vs),float(step));sc,roc,dd,reject=score_result(r,policy)
   c={'entry_trigger':trig,'settings':{'take_profit_pct':tp,'so_deviation_pct':dev,'safety_orders':n,'volume_scale':vs,'step_scale':step},'training_metrics':{**r,'return_on_max_capital_pct':roc,'max_drawdown_pct':dd},'score':sc}
   if reject:continue
   if best is None or sc>best['score']:best=c
 return best,tested
def main():
 kp=load(POLICY);rp=load(RESEARCH);disc=load(DOCS/'coin_discovery.json');kraken=load(DOCS/'walk_forward_registry.json');adaptive=load(DOCS/'adaptive_research_queue.json')
 kr={str(x.get('symbol') or '').replace('XBT','BTC').upper():x for x in kraken.get('coins') or [] if isinstance(x,dict)};adby={str(x.get('asset') or '').upper():x for x in adaptive.get('candidates') or [] if isinstance(x,dict)}
 assets=[]
 for x in (disc.get('researched_candidates') or [])+(disc.get('shortlist') or []):
  a=str(x.get('base_currency') or '').upper()
  if a and a not in assets:assets.append(a)
 assets=assets[:int(kp.get('deep_research_usdt_assets',8))]
 rowsout=[];total=0
 regimes={'BULL':{'BULL','STRONG_BULL'},'ACCUMULATION':{'ACCUMULATION'},'NEUTRAL':{'NEUTRAL'},'BEAR':{'BEAR','DISTRIBUTION','CAPITULATION'}}
 wp=kp['walk_forward'];minbars=int(kp.get('minimum_backtest_bars',900))
 for asset in assets:
  p=data_dir()/f'{asset}-USDT_4H.csv'
  if not p.exists():rowsout.append({'asset':asset,'status':'HISTORY_QUEUED','bars':0});continue
  raw=enrich(load_rows(p));n=len(raw)
  if n<minbars:rowsout.append({'asset':asset,'status':'HISTORY_BUILDING','bars':n,'minimum_bars':minbars,'progress_pct':round(100*n/minbars,1)});continue
  a=max(int(n*float(wp['training_fraction'])),int(wp['minimum_training_bars']));b=max(a+int(n*float(wp['validation_fraction'])),a+int(wp['minimum_validation_bars']));b=min(b,n-int(wp['minimum_forward_bars']))
  if b<=a or n-b<int(wp['minimum_forward_bars']):rowsout.append({'asset':asset,'status':'INSUFFICIENT_SPLIT','bars':n});continue
  train=raw[:a];val=raw[a:b];forward=raw[b:];profiles={}
  current=family(raw[-1].get('regime'))
  for fam,allowed in regimes.items():
   best,tested=train_best(train,allowed,rp,(adby.get(asset) or {}).get('search_extensions'));total+=tested
   if not best:continue
   vm=evaluate(val,best,allowed,rp);fm=evaluate(forward,best,allowed,rp)
   pass_validation=bool(vm and vm['closed_deals']>=3 and vm['mark_to_market_pnl']>0 and vm['longest_hours']<=float(wp['maximum_validation_longest_hours']) and not vm['rejected_for_open_duration'])
   profiles[fam]={'frozen_training_winner':best,'validation_metrics':vm,'forward_observation':fm,'validation_pass':pass_validation}
  cp=profiles.get(current) or {};kucoin_pass=bool(cp.get('validation_pass'))
  k=kr.get(asset) or {};kstatus=str(k.get('status') or 'MISSING').upper()
  status='READY_FOR_MANUAL_REVIEW' if kucoin_pass else 'RESEARCH_PENDING'
  rowsout.append({'asset':asset,'pair':f'{asset}-USDT','status':status,'bars':n,'period':{'start':raw[0]['time'],'end':raw[-1]['time']},
    'split':{'training_bars':len(train),'validation_bars':len(val),'forward_bars':len(forward),'training_end':train[-1]['time'],'validation_end':val[-1]['time']},
    'current_regime_family':current,'current_regime_profile':cp,'regime_profiles':profiles,
    'kucoin_primary_validation_pass':kucoin_pass,'kraken_robustness_status':kstatus,'kraken_used_for_optimisation':False,
    'deployment_gate':'PASS' if kucoin_pass else 'WAIT','adaptive_research_applied':bool(adby.get(asset)),'adaptive_experiments':(adby.get(asset) or {}).get('next_experiments') or [],'manual_approval_required':True})
 ready=sum(1 for x in rowsout if x.get('status')=='READY_FOR_MANUAL_REVIEW')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'mode':'kucoin_primary_frozen_walk_forward','data_source':'KuCoin public 4h candles','training_optimisation_only':True,'freeze_before_validation':True,
  'kraken_role':'independent cross-exchange robustness evidence; not required to create KuCoin-primary research evidence',
  'summary':{'assets':len(rowsout),'ready_for_manual_review':ready,'backtests_run':total},'assets':rowsout,'manual_deployment_only':True}
 payload['snapshot_id']=hashlib.sha256(json.dumps([(x.get('asset'),x.get('status'),x.get('bars')) for x in rowsout],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'KuCoin walk-forward written: {OUT}; ready={ready}/{len(rowsout)}; backtests={total}');return 0
if __name__=='__main__':raise SystemExit(main())
