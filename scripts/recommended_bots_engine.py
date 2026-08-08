#!/usr/bin/env python3
"""V45 explainable recommended-bot packages.
Research evidence, current-regime optimisation status, capital sizing and trade-duration risk are explicit.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'recommended_bots.json'
def load(n):
 try:
  x=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def canonical(raw):
 raw=raw or {};aliases={'base_order_volume':['base_order_volume','base_order'],'safety_order_volume':['safety_order_volume','safety_order'],'take_profit_pct':['take_profit_pct','take_profit'],'so_deviation_pct':['so_deviation_pct','safety_order_deviation_pct','safety_order_step_percentage'],'safety_orders':['safety_orders','max_safety_orders'],'volume_scale':['volume_scale','martingale_volume_coefficient'],'step_scale':['step_scale','martingale_step_coefficient'],'max_active_safety_orders':['max_active_safety_orders'],'max_active_deals':['max_active_deals'],'start_condition':['start_condition'],'order_type':['order_type'],'trailing_enabled':['trailing_enabled'],'cooldown_seconds':['cooldown_seconds']}
 return {k:next((raw.get(n) for n in names if raw.get(n) is not None),None) for k,names in aliases.items()}
def profitability(c):
 q=c.get('q1_2026_metrics') or {};tr=c.get('training_metrics') or {}
 def roc(m):
  pnl=num(m.get('mark_to_market_pnl') if m.get('mark_to_market_pnl') is not None else m.get('net_pnl'));cap=num(m.get('max_capital'));return round(100*pnl/cap,1) if pnl is not None and cap and cap>0 else None
 qroc=roc(q);troc=roc(tr)
 return {'q1_return_on_max_capital_pct':qroc,'q1_validated_return_on_max_capital_pct':qroc,'training_return_on_max_capital_pct':troc,'q1_net_pnl':num(q.get('net_pnl')),'q1_closed_deals':q.get('closed_deals'),'q1_average_hold_hours':num(q.get('average_hours')),'q1_longest_closed_trade_hours':num(q.get('longest_hours')),'q1_ended_with_open_position':bool(q.get('open_position')),'q1_open_pnl':num(q.get('open_pnl')),'training_longest_closed_trade_hours':num(tr.get('longest_hours')),'training_ended_with_open_position':bool(tr.get('open_position')),'label':'Historical validated return on maximum capital; not a future-profit forecast.','worthwhile_indicator':'STRONG_EVIDENCE' if qroc is not None and qroc>=20 else ('POSITIVE_EVIDENCE' if qroc is not None and qroc>0 else 'INSUFFICIENT_EVIDENCE')}
def main():
 pipe=load('research_pipeline.json');capital=load('capital_intelligence.json');portfolio=load('portfolio_intelligence.json');kucoin=load('kucoin_account.json');optim=load('optimisation_queue.json');globalm=load('global_market.json');kuwf=load('kucoin_walk_forward.json');byopt={str(x.get('asset') or '').upper():x for x in optim.get('items') or [] if isinstance(x,dict)};kuby={str(x.get('asset') or '').upper():x for x in kuwf.get('assets') or [] if isinstance(x,dict)}
 deployable=num(capital.get('deployable_capital'));deployable=deployable if deployable is not None else num(portfolio.get('deployable_capital'))
 if deployable is None:
  free=num(kucoin.get('free_usdt'));reserve=num(capital.get('remaining_active_deal_dca_reserve')) or num(portfolio.get('reserved_capital')) or 0
  deployable=max(0,free-reserve) if free is not None else None
 rows=[]
 for c in pipe.get('candidates') or []:
  if not isinstance(c,dict) or c.get('stage')!='READY_FOR_MANUAL_REVIEW':continue
  asset=str(c.get('asset') or '').upper();opt=byopt.get(asset) or {};kw=kuby.get(asset) or {};profile=opt.get('current_regime_profile') or {};raw=(opt.get('recommended_research_settings') or c.get('frozen_settings') or {});settings=canonical(raw);hist=num((c.get('q1_2026_metrics') or {}).get('max_capital')) or num((c.get('training_metrics') or {}).get('max_capital'))
  suggested=round(min(deployable*.20,hist if hist and hist>0 else deployable*.20),2) if deployable is not None and deployable>0 else None
  completeness=sum(v is not None for v in settings.values());prof=profitability(c);opt_status=opt.get('status') or 'OPTIMISATION_PENDING';deployment_ready=bool(opt.get('deployment_candidate'))
  cid=hashlib.sha256(json.dumps({'asset':asset,'settings':settings,'regime':globalm.get('regime')},sort_keys=True,default=str).encode()).hexdigest()[:24]
  rows.append({'candidate_id':cid,'asset':asset,'pair':c.get('pair') or f'{asset}-USDT','state':'DEPLOYMENT_REVIEW_READY' if deployment_ready else 'OPTIMISATION_PENDING','confidence_pct':num(c.get('current_research_score')),'confidence_label':'Research confidence — not expected return.','current_global_regime':globalm.get('regime'),'optimisation_status':opt_status,
   'suggested_pilot_usdt':suggested,'suggested_initial_allocation_usdt':suggested,'allocation_explanation':'Conservative first allocation: up to 20% of currently deployable capital, capped by historical max-capital evidence. Manual approval required.','capital_source':capital.get('capital_source') or ('KuCoin local free USDT minus active-deal DCA reserve' if kucoin.get('free_usdt') is not None else 'Portfolio fallback'),'historical_max_capital':hist,'profitability_evidence':prof,'dca_settings':settings,'settings_completeness_pct':round(100*completeness/len(settings),1) if settings else 0,
   'entry_trigger':profile.get('entry_trigger'),'trade_fluidity':profile.get('trade_fluidity'),'regime_backtest_metrics':profile.get('metrics'),'kucoin_walk_forward_status':kw.get('status'),'kucoin_primary_validation_pass':kw.get('kucoin_primary_validation_pass'),'kraken_q1_status':c.get('walk_forward_status'),'training_metrics':c.get('training_metrics'),'q1_2026_metrics':c.get('q1_2026_metrics'),'evidence_gates':c.get('gates') or {},'manual_approval_required':True,'creates_live_bot':False,
   'process_explanation':['Add to Recommended Bots stages the candidate in the browser while the autonomous research loop continues independently.','Background optimisation tests entry triggers and DCA ladders by regime when comparable data is available.','Settings are frozen before independent validation.','Current KuCoin/global regime is checked before deployment review.','Live deployment remains manual; V49 does not place orders.'],
   'next_step':'Review deployment package and create manually only after regime optimisation is complete.' if deployment_ready else 'Keep in Recommended Bots while background regime optimisation/validation completes.'})
 rows.sort(key=lambda x:((1 if x['state']=='DEPLOYMENT_REVIEW_READY' else 0),x.get('confidence_pct') or -1),reverse=True)
 payload={'schema_version':'1.1','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'explainable_recommended_bot_packages','candidate_count':len(rows),'candidates':rows,'workflow':['RESEARCH','ADD_TO_RECOMMENDED','BACKGROUND_OPTIMISATION','INDEPENDENT_VALIDATION','CURRENT_REGIME_CHECK','MANUAL_DEPLOYMENT_REVIEW'],'read_only':True,'automatic_live_deployment':False}
 payload['snapshot_id']=hashlib.sha256(json.dumps([x['candidate_id'] for x in rows],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Recommended bots written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
