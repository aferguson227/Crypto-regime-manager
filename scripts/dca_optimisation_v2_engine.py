#!/usr/bin/env python3
"""V62 DCA Optimisation 2.0 — capital sizing validation.

The existing KuCoin walk-forward engine already optimises entry trigger, TP, SO
deviation, ladder depth, volume scale and step scale on training data, then freezes
them before unseen validation.

V62 adds a second training-only optimisation for BO/SO sizing. The winning sizing
is frozen and re-tested on the same unseen KuCoin validation segment. Execution
controls that do not exist in the replay model (max concurrent SOs, order type,
trailing and cooldown) are NEVER labelled optimised; they remain governed controls.

No live changes are made.
"""
from __future__ import annotations
import json,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.regime_backtest_engine import load_rows,enrich,replay,score_result

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'dca_optimisation_v2.json';POL=ROOT/'config'/'research_policy.json';KPOL=ROOT/'config'/'kucoin_research_policy.json'

def loadj(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_dir():
 raw=os.getenv('CRM_DATA_ROOT');base=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 return base/'KuCoin'/'4h'
def allowed(fam):
 return {'BULL':{'BULL','STRONG_BULL'},'ACCUMULATION':{'ACCUMULATION'},'NEUTRAL':{'NEUTRAL'},'BEAR':{'BEAR','DISTRIBUTION','CAPITULATION'}}.get(fam,{fam})
def main():
 wf=loadj(DOCS/'kucoin_walk_forward.json');rp=loadj(POL);kp=loadj(KPOL);rowsout=[];tested_total=0
 bo_grid=[50.0,100.0,150.0];so_grid=[50.0,100.0,150.0]
 for x in wf.get('assets') or []:
  asset=str(x.get('asset') or '').upper();cp=x.get('current_regime_profile') or {};winner=cp.get('frozen_training_winner') or {}
  st=winner.get('settings') or {};trigger=winner.get('entry_trigger');fam=x.get('current_regime_family')
  p=data_dir()/f'{asset}-USDT_4H.csv'
  rec={'asset':asset,'pair':f'{asset}-USDT','current_regime':fam,'source_walk_forward_status':x.get('status'),
       'structural_settings':st,'entry_trigger':trigger,'optimisation_dimensions':['base_order_volume','safety_order_volume'],
       'already_optimised_dimensions':['entry_trigger','take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale'],
       'governed_not_optimised':['max_active_safety_orders','max_active_deals','order_type','trailing_enabled','cooldown_seconds'],
       'automatic_live_changes':False}
  if not p.exists() or not st or not trigger or not fam:
   rec.update({'optimisation_status':'WAITING_FOR_RESEARCH_INPUT','progress_pct':0,'reason':'Frozen KuCoin structural winner/history is not available yet.'});rowsout.append(rec);continue
  raw=enrich(load_rows(p));split=x.get('split') or {};train_n=int(split.get('training_bars') or 0);val_n=int(split.get('validation_bars') or 0)
  if train_n<=0 or val_n<=0 or len(raw)<train_n+val_n:
   rec.update({'optimisation_status':'WAITING_FOR_SPLIT','progress_pct':10,'reason':'KuCoin training/validation split is incomplete.'});rowsout.append(rec);continue
  train=raw[:train_n];val=raw[train_n:train_n+val_n];allow=allowed(fam);best=None;tested=0
  for bo in bo_grid:
   for so in so_grid:
    tested+=1;tested_total+=1
    r=replay(train,trigger,allow,float(st['take_profit_pct'])/100,float(st['so_deviation_pct'])/100,int(st['safety_orders']),float(st['volume_scale']),float(st['step_scale']),bo=bo,so=so)
    sc,roc,dd,reject=score_result(r,rp)
    c={'base_order_volume':bo,'safety_order_volume':so,'training_score':sc,'training_return_on_max_capital_pct':roc,'training_drawdown_pct':dd,'training_metrics':r,'rejected_for_open_duration':reject}
    if reject:continue
    if best is None or c['training_score']>best['training_score']:best=c
  if not best:
   rec.update({'optimisation_status':'NO_ACCEPTABLE_SIZING','progress_pct':100,'tested_combinations':tested,'reason':'All BO/SO sizing variants failed the training duration/risk rules.'});rowsout.append(rec);continue
  vm=replay(val,trigger,allow,float(st['take_profit_pct'])/100,float(st['so_deviation_pct'])/100,int(st['safety_orders']),float(st['volume_scale']),float(st['step_scale']),bo=best['base_order_volume'],so=best['safety_order_volume'])
  sc,roc,dd,reject=score_result(vm,rp);maxh=float((kp.get('walk_forward') or {}).get('maximum_validation_longest_hours',168))
  passed=bool(vm.get('closed_deals',0)>=3 and vm.get('mark_to_market_pnl',0)>0 and vm.get('longest_hours',99999)<=maxh and not reject)
  strategy={'entry_trigger':trigger,'take_profit_pct':st.get('take_profit_pct'),'so_deviation_pct':st.get('so_deviation_pct'),
            'safety_orders':st.get('safety_orders'),'volume_scale':st.get('volume_scale'),'step_scale':st.get('step_scale'),
            'base_order_volume':best['base_order_volume'],'safety_order_volume':best['safety_order_volume']}
  controls={'max_active_safety_orders':min(3,int(st.get('safety_orders') or 1)),'max_active_deals':1,
            'order_type':'market base order / limit DCA orders','trailing_enabled':False,'cooldown_seconds':0}
  rec.update({'optimisation_status':'COMPLETE' if passed else 'UNSEEN_VALIDATION_FAILED','progress_pct':100,
              'tested_combinations':tested,'winning_strategy_settings':strategy,'governed_execution_controls':controls,
              'setting_sources':{**{k:'OPTIMISED_AND_UNSEEN_VALIDATED' for k in strategy},**{k:'GOVERNED_POLICY_NOT_OPTIMISED' for k in controls}},
              'training_winner':best,'unseen_validation_metrics':{**vm,'return_on_max_capital_pct':roc,'max_drawdown_pct':dd,'score':sc},
              'unseen_validation_pass':passed,'capital_required_usdt':vm.get('max_capital'),
              'reason':('BO/SO sizing passed unseen KuCoin validation.' if passed else 'Winning training sizing did not pass unseen KuCoin validation; CRM will not present it as deployment-ready.')})
  rowsout.append(rec)
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
          'mode':'training-only BO/SO sizing optimisation -> freeze -> unseen KuCoin validation',
          'assets':rowsout,'summary':{'assets':len(rowsout),'complete':sum(x.get('optimisation_status')=='COMPLETE' for x in rowsout),
                                     'incomplete':sum(x.get('optimisation_status')!='COMPLETE' for x in rowsout),'backtests_run':tested_total},
          'truthfulness_policy':'Only replay-tested/frozen/validated strategy settings are called optimised. Execution-only controls are labelled governed and not optimised.',
          'manual_deployment_only':True}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"DCA Optimisation 2.0: complete={payload['summary']['complete']}/{payload['summary']['assets']}; backtests={tested_total}")
 return 0
if __name__=='__main__':raise SystemExit(main())
