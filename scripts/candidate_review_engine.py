#!/usr/bin/env python3
"""V51 explainable candidate review packages with profitability, continuation and regime profiles."""
from __future__ import annotations
import json,math
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
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def days_between(a,b):
 try:return round((datetime.fromisoformat(str(b).replace('Z','+00:00'))-datetime.fromisoformat(str(a).replace('Z','+00:00'))).total_seconds()/86400,1)
 except:return None
def main():
 wf=load('kucoin_walk_forward.json');bots=load('recommended_bots.json');alloc=load('portfolio_allocation_recommendations.json');adaptive=load('adaptive_research_queue.json')
 hist=load('historical_data_status.json');kr=load('walk_forward_registry.json');res=load('validation_resolution.json');cont=load('cross_exchange_continuation.json');sched=load('research_scheduler_status.json');grades=load('candidate_evidence_grades.json');p=loadp()
 bybot={str(x.get('asset') or '').upper():x for x in bots.get('candidates') or []};bya={str(x.get('asset') or '').upper():x for x in alloc.get('recommendations') or []};byad={str(x.get('asset') or '').upper():x for x in adaptive.get('candidates') or []}
 bykr={str(x.get('symbol') or '').replace('XBT','BTC').upper():x for x in kr.get('coins') or []};byres={str(x.get('asset') or '').upper():x for x in res.get('positions') or []};bycont={str(x.get('asset') or '').upper():x for x in cont.get('assets') or []};bygrade={str(x.get('asset') or '').upper():x for x in grades.get('assets') or []};hinv={str(x.get('symbol') or '').split('-')[0].upper():x for x in hist.get('inventory') or []}
 rows=[]
 for x in wf.get('assets') or []:
  a=str(x.get('asset') or '').upper();cp=x.get('current_regime_profile') or {};vm=cp.get('validation_metrics') or {};fm=cp.get('forward_observation') or {};bot=bybot.get(a) or {};al=bya.get(a) or {};ad=byad.get(a) or {};k=bykr.get(a) or {};rr=byres.get(a) or {};co=bycont.get(a) or {};eg=bygrade.get(a) or {};hi=hinv.get(a) or {}
  observation_days=days_between((x.get('split') or {}).get('validation_end'),(x.get('period') or {}).get('end'));maxcap=num(vm.get('max_capital')) or 0;ret=(100*(num(vm.get('mark_to_market_pnl')) or 0)/maxcap) if maxcap else None;dd=(100*abs(num(vm.get('max_drawdown_dollars')) or 0)/maxcap) if maxcap else None
  fcap=num(fm.get('max_capital')) or maxcap;fret=(100*(num(fm.get('mark_to_market_pnl')) or 0)/fcap) if fcap else None
  annual=None
  if ret is not None:
   vdays=days_between((x.get('split') or {}).get('training_end'),(x.get('split') or {}).get('validation_end'))
   if vdays and vdays>=30:annual=round(ret*365/vdays,1)
  gates=[
   {'id':'evidence_grade','label':'Evidence grade','state':'PASS' if eg.get('deployment_history_gate')=='PASS' else 'BLOCKED','detail':f"{eg.get('evidence_grade','Unknown')} · {eg.get('history_years',0)} years · {eg.get('bars_4h',0)} 4h bars. {eg.get('reason','')}"},
   {'id':'history_complete','label':'Historical data','state':'PASS' if (hi.get('bars') or x.get('bars') or 0)>=900 else 'PENDING','detail':f"{hi.get('bars') or x.get('bars') or 0} 4h bars available."},
   {'id':'kucoin_walk_forward','label':'KuCoin walk-forward','state':'PASS' if x.get('kucoin_primary_validation_pass') else 'PENDING','detail':'Frozen settings passed unseen KuCoin validation.' if x.get('kucoin_primary_validation_pass') else 'No current-regime frozen configuration has passed unseen KuCoin validation yet.'},
   {'id':'trade_fluidity','label':'Trade fluidity','state':'PASS' if vm and not vm.get('open_position') and float(vm.get('longest_hours') or 9999)<=168 else 'PENDING','detail':f"Longest validation trade {vm.get('longest_hours','unknown')}h; open position {vm.get('open_position','unknown')}."},
   {'id':'current_regime_fit','label':'Current regime fit','state':'PASS' if cp and x.get('kucoin_primary_validation_pass') else 'PENDING','detail':f"Current regime family: {x.get('current_regime_family') or 'unknown'}."},
   {'id':'capital_allocation','label':'Capital allocation','state':'PASS' if al.get('recommended_allocation_usdt') is not None else 'PENDING','detail':al.get('reason') or 'Awaiting canonical deployable-capital calculation.'}
  ]
  passed=sum(g['state']=='PASS' for g in gates);score=round(100*passed/len(gates),1)
  krstatus=str(k.get('status') or x.get('kraken_robustness_status') or 'MISSING').upper();kq=k.get('q1_2026_metrics') or {}
  if krstatus=='PASS':krwhy='Independent Kraken Q1 evidence supported the frozen historical configuration.'
  elif krstatus=='FAIL':
   krwhy=f"Kraken cutoff failed: mark-to-market P/L {kq.get('mark_to_market_pnl','unknown')}; open position {kq.get('open_position','unknown')}."
   if co:krwhy+=' '+('Later KuCoin continuation closed that same reconstructed position.' if co.get('continuation_status')=='CLOSED_ON_KUCOIN_CONTINUATION' else f"Continuation status: {co.get('continuation_status')}.")
   krwhy+=' Original Kraken failure remains preserved and lowers robustness confidence.'
  else:krwhy='No comparable Kraken robustness result is available; KuCoin remains the primary deployment dataset.'
  if score==100:recommendation='READY_FOR_MANUAL_REVIEW';next_action='Review the evidence/settings package and choose Prepare deployment, Continue monitoring or Remove.'
  elif ad:recommendation='ADAPTIVE_RESEARCH';next_action='Continue monitoring while CRM runs failure-specific experiments and re-validates on unseen KuCoin data.'
  else:recommendation='CONTINUE_RESEARCH';next_action='Continue monitoring until outstanding automatic evidence gates pass.'
  target=float((p.get('monitoring') or {}).get('preferred_forward_observation_days',14));monitor_complete=bool(observation_days is not None and observation_days>=target);monitor_pct=round(min(100,100*(observation_days or 0)/target),1) if target else None
  if ad:
   stages=[('Diagnosis',True),('Experiment design',True),('Optimisation',bool(x.get('adaptive_research_applied'))),('Unseen validation',bool(x.get('adaptive_research_applied') and x.get('kucoin_primary_validation_pass'))),('Regime verification',bool(x.get('kucoin_primary_validation_pass')))]
  else:stages=[('History',gates[0]['state']=='PASS'),('Optimisation',bool(cp)),('Unseen validation',gates[1]['state']=='PASS'),('Trade fluidity',gates[2]['state']=='PASS'),('Regime verification',gates[3]['state']=='PASS')]
  done=sum(v for _,v in stages);progress=round(100*done/len(stages),1);remaining=len(stages)-done
  regime_profiles={}
  for name,pr in (x.get('regime_profiles') or {}).items():
   frozen=(pr.get('frozen_training_winner') or {});regime_profiles[name]={'validated':bool(pr.get('validation_pass')),'entry_trigger':frozen.get('entry_trigger'),'settings':frozen.get('settings') or {},'validation_metrics':pr.get('validation_metrics') or {},'forward_observation':pr.get('forward_observation') or {}}
  rows.append({'asset':a,'pair':x.get('pair') or f'{a}-USDT','evidence_grade':eg,'readiness_pct':score,'gates':gates,'recommendation':recommendation,'next_action':next_action,'current_regime':x.get('current_regime_family'),
   'settings':((cp.get('frozen_training_winner') or {}).get('settings') or bot.get('dca_settings') or {}),'entry_trigger':(cp.get('frozen_training_winner') or {}).get('entry_trigger') or bot.get('entry_trigger'),
   'kucoin_profitability':{'validation_return_on_max_capital_pct':round(ret,2) if ret is not None else None,'validation_mark_to_market_pnl':vm.get('mark_to_market_pnl'),'validation_closed_deals':vm.get('closed_deals'),
    'validation_average_hold_hours':vm.get('average_hours'),'validation_p90_hold_hours':vm.get('p90_hours'),'validation_longest_hold_hours':vm.get('longest_hours'),'validation_drawdown_pct':round(dd,2) if dd is not None else None,
    'forward_return_on_max_capital_pct':round(fret,2) if fret is not None else None,'historical_annualised_equivalent_pct':annual,'annualised_label':'Historical annualised equivalent; not a forecast.' if annual is not None else None},
   'validation_metrics':vm,'forward_observation':fm,'forward_observation_days':observation_days,'monitoring_target_days':target,'monitoring_progress_pct':monitor_pct,'monitoring_complete':monitor_complete,
   'monitoring_explanation':(f'Preferred observation requirement complete: {observation_days} days available versus {target:g} days preferred.' if monitor_complete else f'{observation_days or 0} of {target:g} preferred observation days recorded.'),
   'research_progress':{'progress_pct':progress,'stages':[{'label':n,'complete':v} for n,v in stages],'remaining_stages':remaining,'estimated_remaining_cycles':0 if remaining==0 else max(1,min(remaining,3)),'typical_cycle_seconds':sched.get('typical_cycle_seconds')},
   'suggested_allocation_usdt':al.get('recommended_allocation_usdt'),'allocation_reason':al.get('reason'),'validation_cutoff':{'state':rr.get('validation_cutoff_state'),'post_validation_resolution':rr.get('post_validation_resolution'),'original_validation_preserved':rr.get('original_validation_preserved',True)},
   'kraken_robustness':{'status':krstatus,'explanation':krwhy,'continuation':co or None},'adaptive_research':ad or None,'regime_profiles':regime_profiles,
   'deployment_preparation_available':score==100,'automatic_deployment':False})
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'candidates':rows,
  'summary':{'candidates':len(rows),'ready_for_manual_review':sum(x['readiness_pct']==100 for x in rows),'adaptive_research':sum(bool(x['adaptive_research']) for x in rows)},
  'workflow':['Continue research','Ready for manual review','Prepare deployment','Shadow execution review','Manual confirmation','Future direct execution'],'automatic_live_deployment':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Candidate review written: {OUT}; ready={payload["summary"]["ready_for_manual_review"]}/{len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
