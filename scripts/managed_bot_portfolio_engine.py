#!/usr/bin/env python3
"""V67 managed bot portfolio.

Combines live production bots, forward paper bots and validated deployment
candidates into one trader-focused portfolio view. Advisory/read-only.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'managed_bot_portfolio.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v)
 except:return None
def main():
 live=load('live_portfolio_truth.json');profiles=load('live_bot_profiles.json');reval=load('live_strategy_revalidation.json');paper=load('paper_portfolio.json');registry=load('managed_bot_registry.json')
 life=load('deployment_lifecycle.json');review=load('candidate_review.json');cap=load('portfolio_capital_v2.json')
 pby={str(x.get('asset') or '').upper():x for x in paper.get('bots') or []};managed_assets={str(x).upper() for x in registry.get('assets') or []}
 lby={str(x.get('asset') or '').upper():x for x in live.get('deals') or []}
 prof={str(x.get('asset') or '').upper():x for x in profiles.get('bots') or []};vby={str(x.get('asset') or '').upper():x for x in reval.get('live_bots') or []}
 rby={str(x.get('asset') or '').upper():x for x in review.get('candidates') or []}
 rows=[];seen=set()
 # Production first.
 for a,d in lby.items():
  if d.get('effective_position_state')!='OPEN':continue
  pr=prof.get(a) or {};ls=pr.get('live_settings') or {};rec=pr.get('recommended_current_regime') or {}
  rows.append({'asset':a,'state':'LIVE','bot_name':d.get('bot_name'),'position_quote':d.get('position_cost_basis_quote') or d.get('capital_used_quote'),
   'open_pnl_quote':d.get('open_pnl_quote'),'open_pnl_pct':d.get('profit_pct'),'safety_orders_filled':d.get('completed_safety_orders'),
   'max_safety_orders':d.get('max_safety_orders') or ls.get('safety_orders'),'active_safety_orders':d.get('active_safety_orders'),
   'average_entry':d.get('average_entry'),'current_price':d.get('open_pnl_price'),'reserved_quote':d.get('remaining_dca_reserve_quote'),
   'current_regime':pr.get('current_regime'),'latest_validated':bool((rec or {}).get('validated')),
   'would_deploy_today':(vby.get(a) or {}).get('would_deploy_today'),'next_action':'KEEP_ACTIVE_DEAL','settings':ls,'managed':True,'source':'KuCoin + provider reconciliation'});seen.add(a)
 # Paper / candidate rows.
 for b in life.get('bots') or []:
  a=str(b.get('asset') or '').upper()
  if not a or a in seen:continue
  pp=pby.get(a) or {};rv=rby.get(a) or {}
  state='PAPER' if pp else ('READY' if b.get('lifecycle_state') in {'READY_TO_DEPLOY','READY_FOR_DEPLOYMENT_REVIEW'} else 'RESEARCH')
  rows.append({'asset':a,'state':state,'bot_name':f'{a} DCA','position_quote':pp.get('position_quote'),'open_pnl_quote':pp.get('open_pnl_quote'),
   'open_pnl_pct':pp.get('open_pnl_pct'),'safety_orders_filled':pp.get('safety_orders_filled'),'max_safety_orders':pp.get('max_safety_orders'),
   'active_safety_orders':None,'average_entry':pp.get('average_entry'),'current_price':pp.get('current_price'),'reserved_quote':b.get('capital_required_usdt'),
   'current_regime':b.get('current_regime'),'latest_validated':b.get('dca_optimisation_status')=='COMPLETE',
   'paper_closed_deals':pp.get('closed_deals'),'paper_realised_pnl_quote':pp.get('realised_pnl_quote'),'paper_win_rate_pct':pp.get('win_rate_pct'),
   'paper_days':pp.get('paper_days'),'paper_profit_per_day_quote':pp.get('profit_per_day_quote'),'paper_max_drawdown_quote':pp.get('max_drawdown_quote'),
   'next_action':b.get('recommended_action'),'capital_required_usdt':b.get('capital_required_usdt'),
   'safe_allocation_usdt':b.get('allocation_usdt'),'readiness_pct':rv.get('readiness_pct'),'settings':b.get('settings') or pp.get('settings'),
   'managed':a in managed_assets,'source':'Forward paper trading + deployment lifecycle'});seen.add(a)
 # Rank non-live candidates transparently.
 candidates=[x for x in rows if x['state'] in {'PAPER','READY'}]
 for x in candidates:
  rv=rby.get(x['asset']) or {};kr=(rv.get('kucoin_profitability') or {});ret=num(kr.get('validation_return_on_max_capital_pct')) or num(kr.get('validation_return_pct')) or num(rv.get('kucoin_validation_return_pct')) or 0
  paper_pct=num(x.get('open_pnl_pct')) or 0;readiness=num(x.get('readiness_pct')) or 0
  x['portfolio_priority_score']=round(readiness*0.5+min(max(ret,0),300)*0.12+max(min(paper_pct,25),-25)*0.3,2)
 for i,x in enumerate(sorted(candidates,key=lambda r:r.get('portfolio_priority_score',0),reverse=True),1):x['portfolio_rank']=i
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'bots':rows,'summary':{'total_managed':sum(bool(x.get('managed')) for x in rows),'live':sum(x['state']=='LIVE' for x in rows),'paper':sum(x['state']=='PAPER' and x.get('managed') for x in rows),
                         'ready':sum(x['state']=='READY' for x in rows),'research':sum(x['state']=='RESEARCH' for x in rows)},
  'capital':{'conservative_safe_usdt':cap.get('safe_multi_bot_pool_usdt'),'conditional_capacity_usdt':cap.get('conditional_multi_bot_capacity_usdt'),
             'worst_case_headroom_usdt':cap.get('worst_case_headroom_usdt')},
  'principle':'My Bots combines live, forward-paper and validated strategies. Ranking is advisory and cannot deploy capital automatically.',
  'automatic_live_execution':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"Managed Bot Portfolio: live={payload['summary']['live']} paper={payload['summary']['paper']} ready={payload['summary']['ready']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
