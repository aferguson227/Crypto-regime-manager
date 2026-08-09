#!/usr/bin/env python3
"""V50 candidate decision workflow and explainable review packages."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'candidate_review.json';POL=ROOT/'config'/'v50_decision_policy.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def loadp():
 try:return json.loads(POL.read_text(encoding='utf-8-sig'))
 except:return {}
def days_between(a,b):
 try:
  x=datetime.fromisoformat(str(a).replace('Z','+00:00'));y=datetime.fromisoformat(str(b).replace('Z','+00:00'));return round((y-x).total_seconds()/86400,1)
 except:return None
def main():
 wf=load('kucoin_walk_forward.json');bots=load('recommended_bots.json');alloc=load('portfolio_allocation_recommendations.json')
 adaptive=load('adaptive_research_queue.json');hist=load('historical_data_status.json');kr=load('walk_forward_registry.json');res=load('validation_resolution.json');p=loadp()
 bybot={str(x.get('asset') or '').upper():x for x in bots.get('candidates') or []};bya={str(x.get('asset') or '').upper():x for x in alloc.get('recommendations') or []}
 byad={str(x.get('asset') or '').upper():x for x in adaptive.get('candidates') or []};bykr={str(x.get('symbol') or '').replace('XBT','BTC').upper():x for x in kr.get('coins') or []};byres={str(x.get('asset') or '').upper():x for x in res.get('positions') or []}
 hinv={str(x.get('symbol') or '').split('-')[0].upper():x for x in hist.get('inventory') or []};rows=[]
 for x in wf.get('assets') or []:
  a=str(x.get('asset') or '').upper();cp=x.get('current_regime_profile') or {};vm=cp.get('validation_metrics') or {};fm=cp.get('forward_observation') or {};bot=bybot.get(a) or {};al=bya.get(a) or {};ad=byad.get(a) or {};k=bykr.get(a) or {};rr=byres.get(a) or {};hi=hinv.get(a) or {}
  observation_days=days_between((x.get('split') or {}).get('validation_end'),(x.get('period') or {}).get('end'))
  gates=[
   {'id':'history_complete','label':'Historical data','state':'PASS' if (hi.get('bars') or x.get('bars') or 0)>=900 else 'PENDING','detail':f"{hi.get('bars') or x.get('bars') or 0} 4h bars available."},
   {'id':'kucoin_walk_forward','label':'KuCoin walk-forward','state':'PASS' if x.get('kucoin_primary_validation_pass') else 'PENDING','detail':'Frozen settings passed unseen KuCoin validation.' if x.get('kucoin_primary_validation_pass') else 'No current-regime frozen configuration has passed unseen KuCoin validation yet.'},
   {'id':'trade_fluidity','label':'Trade fluidity','state':'PASS' if vm and not vm.get('open_position') and float(vm.get('longest_hours') or 9999)<=168 else 'PENDING','detail':f"Longest validation trade {vm.get('longest_hours','unknown')}h; open position {vm.get('open_position','unknown')}."},
   {'id':'current_regime_fit','label':'Current regime fit','state':'PASS' if cp and x.get('kucoin_primary_validation_pass') else 'PENDING','detail':f"Current regime family: {x.get('current_regime_family') or 'unknown'}."},
   {'id':'capital_allocation','label':'Capital allocation','state':'PASS' if al.get('recommended_allocation_usdt') is not None else 'PENDING','detail':al.get('reason') or 'Awaiting canonical deployable-capital calculation.'}
  ]
  passed=sum(g['state']=='PASS' for g in gates);score=round(100*passed/len(gates),1)
  krstatus=str(k.get('status') or x.get('kraken_robustness_status') or 'MISSING').upper();kq=k.get('q1_2026_metrics') or {}
  if krstatus=='PASS':krwhy='Independent Kraken Q1 evidence supported the frozen historical configuration.'
  elif krstatus=='FAIL':krwhy=f"Independent Kraken evidence did not reproduce robustly: mark-to-market P/L {kq.get('mark_to_market_pnl','unknown')}; open position {kq.get('open_position','unknown')}. This lowers confidence but does not automatically veto a KuCoin pass."
  else:krwhy='No comparable Kraken robustness result is available; KuCoin remains the primary deployment dataset.'
  if score==100:recommendation='READY_FOR_MANUAL_REVIEW';next_action='Review the complete evidence/settings package and choose Prepare deployment, Continue monitoring or Remove.'
  elif ad:recommendation='ADAPTIVE_RESEARCH';next_action='Continue monitoring while CRM runs the queued failure-specific experiments on the next research cycle.'
  else:recommendation='CONTINUE_RESEARCH';next_action='Continue monitoring until the outstanding automatic evidence gates pass.'
  target=float((p.get('monitoring') or {}).get('preferred_forward_observation_days',14));monitor_pct=round(min(100,100*(observation_days or 0)/target),1) if target else None
  rows.append({'asset':a,'pair':x.get('pair') or f'{a}-USDT','readiness_pct':score,'gates':gates,'recommendation':recommendation,'next_action':next_action,
   'current_regime':x.get('current_regime_family'),'settings':((cp.get('frozen_training_winner') or {}).get('settings') or bot.get('dca_settings') or {}),
   'entry_trigger':(cp.get('frozen_training_winner') or {}).get('entry_trigger') or bot.get('entry_trigger'),
   'validation_metrics':vm,'forward_observation':fm,'forward_observation_days':observation_days,'monitoring_target_days':target,'monitoring_progress_pct':monitor_pct,
   'suggested_allocation_usdt':al.get('recommended_allocation_usdt'),'allocation_reason':al.get('reason'),
   'validation_cutoff':{'state':rr.get('validation_cutoff_state'),'post_validation_resolution':rr.get('post_validation_resolution'),'original_validation_preserved':rr.get('original_validation_preserved',True)},
   'kraken_robustness':{'status':krstatus,'explanation':krwhy},'adaptive_research':ad or None,'deployment_preparation_available':score==100,'automatic_deployment':False})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'candidates':rows,
  'summary':{'candidates':len(rows),'ready_for_manual_review':sum(x['readiness_pct']==100 for x in rows),'adaptive_research':sum(bool(x['adaptive_research']) for x in rows)},
  'workflow':['Continue research','Ready for manual review','Prepare deployment','Manual confirmation','Deploy through execution provider (future gated capability)'],'automatic_live_deployment':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Candidate review written: {OUT}; ready={payload["summary"]["ready_for_manual_review"]}/{len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
