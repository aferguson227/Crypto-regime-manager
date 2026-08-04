from __future__ import annotations
import json, re, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .data_import import import_file, csv_sources
from .backtest_lab import optimise, replay, load

def symbol_key(name:str)->str:
 m=re.search(r'([A-Z0-9]{2,12})(USD|USDT|USDC)',Path(name).stem.upper())
 return m.group(1) if m else Path(name).stem.upper()

def run_walk_forward(root:Path,training_dir:Path,validation_dir:Path)->dict[str,Any]:
 norm_train=root/'data'/'research'/'training_4h'; norm_val=root/'data'/'research'/'validation_4h'
 norm_train.mkdir(parents=True,exist_ok=True); norm_val.mkdir(parents=True,exist_ok=True)
 results=[]
 with tempfile.TemporaryDirectory(prefix='crm_walk_forward_') as td:
  workspace=Path(td)
  train_files={symbol_key(p.name):p for p in csv_sources(training_dir,workspace/'training')}
  val_files={symbol_key(p.name):p for p in csv_sources(validation_dir,workspace/'validation')}
  for symbol in sorted(set(train_files)&set(val_files)):
   try:
    tr=import_file(train_files[symbol],norm_train); va=import_file(val_files[symbol],norm_val)
    candidates=optimise(Path(tr.output_path)); best=candidates[0]
    s=best['settings']; val_rows=load(Path(va.output_path))
    vr=replay(val_rows,s['take_profit_pct']/100,s['so_deviation_pct']/100,int(s['safety_orders']),float(s['volume_scale']),float(s['step_scale']))
    passed=(vr['closed_deals']>=5 and vr['mark_to_market_pnl']>0 and vr['open_pnl']>=-0.15*vr['max_capital'] and vr['max_drawdown_dollars']>=-0.35*vr['max_capital'])
    results.append({'symbol':symbol,'status':'PASS' if passed else 'FAIL','training_file':train_files[symbol].name,'validation_file':val_files[symbol].name,'training_import':tr.as_dict(),'validation_import':va.as_dict(),'frozen_settings':s,'training_metrics':{k:best[k] for k in ('net_pnl','closed_deals','average_hours','longest_hours','max_drawdown_dollars','max_capital','open_position','score')},'q1_2026_metrics':vr,'next_stage':'FORWARD VALIDATION' if passed else 'RESEARCH / REJECT','production_eligible':False})
   except Exception as e: results.append({'symbol':symbol,'status':'ERROR','error':f'{type(e).__name__}: {e}','production_eligible':False})
 payload={'version':'30.1.0','generated_at':datetime.now(timezone.utc).isoformat(),'method':'Optimise only through Q4 2025; freeze settings; evaluate once on Q1 2026','coins':results,'summary':{'matched':len(results),'passed':sum(x.get('status')=='PASS' for x in results),'failed':sum(x.get('status')=='FAIL' for x in results),'errors':sum(x.get('status')=='ERROR' for x in results)},'safeguards':{'automatic_bot_creation':False,'automatic_3commas_changes':False,'manual_approval_required':True,'q1_used_for_optimisation':False}}
 out=root/'docs'/'walk_forward_registry.json';out.write_text(json.dumps(payload,indent=2),encoding='utf-8');return payload
