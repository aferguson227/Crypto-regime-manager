#!/usr/bin/env python3
"""V50 adaptive candidate research planner.

Failed candidates are not silently discarded. CRM explains the failure and creates
a bounded next-experiment search-space extension for the next cached walk-forward cycle.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'adaptive_research_queue.json';POL=ROOT/'config'/'v50_decision_policy.json'
def load(p):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {}
def now():return datetime.now(timezone.utc).isoformat()
def main():
 wf=load(DOCS/'kucoin_walk_forward.json');kr=load(DOCS/'walk_forward_registry.json');res=load(DOCS/'validation_resolution.json');pol=load(POL)
 krby={str(x.get('symbol') or '').replace('XBT','BTC').upper():x for x in kr.get('coins') or []};rby={str(x.get('asset') or '').upper():x for x in res.get('positions') or []}
 rows=[]
 for x in wf.get('assets') or []:
  asset=str(x.get('asset') or '').upper()
  if not asset or x.get('status')=='READY_FOR_MANUAL_REVIEW':continue
  cp=x.get('current_regime_profile') or {};vm=cp.get('validation_metrics') or {};reasons=[];experiments=[]
  if vm.get('open_position') or (rby.get(asset) or {}).get('validation_cutoff_state')=='OPEN':
   reasons.append('Validation ended with unresolved exposure or current profile retained an open position.')
   experiments += ['tighten_entry_filter','widen_safety_ladder','penalise_long_holds']
  if float(vm.get('max_drawdown_pct') or 0)>20:
   reasons.append(f"Validation drawdown {float(vm.get('max_drawdown_pct') or 0):.1f}% exceeds preferred tolerance.")
   experiments += ['reduce_volume_scale','increase_step_scale','restrict_regime']
  if float(vm.get('longest_hours') or 0)>168:
   reasons.append(f"Longest validation trade {float(vm.get('longest_hours') or 0):.0f}h exceeds the preferred 168h fluidity target.")
   experiments += ['tighten_entry_filter','increase_step_scale','restrict_regime']
  k=krby.get(asset) or {}
  if str(k.get('status') or '').upper()=='FAIL':
   q=k.get('q1_2026_metrics') or {}
   reasons.append(f"Kraken robustness failed: Q1 mark-to-market P/L {q.get('mark_to_market_pnl','unknown')}, open position {q.get('open_position','unknown')}.")
   experiments += ['compare_cross_exchange_failure_reason','lower_cross_exchange_confidence']
  experiments=list(dict.fromkeys(experiments))
  if reasons:
   rows.append({'asset':asset,'pair':x.get('pair') or f'{asset}-USDT','state':'ADAPTIVE_RESEARCH_QUEUED','failure_reasons':reasons,
    'next_experiments':experiments,'search_extensions':{
      'so_deviation_pct':[3.0,5.0,6.0] if 'widen_safety_ladder' in experiments else [],
      'safety_orders':[8,9] if 'widen_safety_ladder' in experiments else [],
      'volume_scale':[1.1,1.2] if 'reduce_volume_scale' in experiments else [],
      'step_scale':[1.3,1.5] if 'increase_step_scale' in experiments else [],
      'entry_triggers':['trend_pullback','qfl_proxy_3','mean_reversion'] if 'tighten_entry_filter' in experiments else []
    },'principle':'Any new configuration must be selected on training data and re-tested on unseen KuCoin validation data.'})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'enabled':True,'queued_count':len(rows),'candidates':rows,
  'automatic_deployment':False,'note':'Adaptive research changes the next experiment, never the frozen historical result.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Adaptive research queue written: {OUT}; queued={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
