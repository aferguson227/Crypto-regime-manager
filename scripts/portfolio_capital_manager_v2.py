#!/usr/bin/env python3
"""V63 Portfolio Capital Manager 2.0.

Separates hard exchange commitments from prudent contingency reserve so one live
DCA bot does not automatically monopolise every free USDT. Advisory/read-only.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'portfolio_capital_v2.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def n(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def main():
 cap=load('capital_intelligence.json');live=load('live_portfolio_truth.json');spec=load('dca_deployment_specs.json');profiles=load('live_bot_profiles.json')
 free=n(cap.get('free_available'));equity=n(cap.get('exchange_equity'));hard=n(cap.get('placed_order_reserve')) or 0
 theoretical=n(cap.get('remaining_active_deal_dca_reserve')) or n(cap.get('reserved_capital')) or 0
 # Preserve a hard worst-case figure, but use a prudent multi-bot reserve for advisory allocation.
 # Conservative pool keeps the existing strong protection rule.
 contingency=max(hard, theoretical*.65)
 safety=(equity*.10 if equity is not None else (free*.10 if free is not None else 0))
 deploy=max(0,free-hard-contingency-safety) if free is not None else None
 # Conditional scenario uses the validated current-regime average SO depth for planning only.
 expected_reserve=0.0
 for b in profiles.get('bots') or []:
  if not b.get('enabled'):continue
  ls=b.get('live_settings') or {};rp=b.get('recommended_current_regime') or {};m=rp.get('metrics') or {}
  so=n(ls.get('safety_order_volume')) or 0;vs=n(ls.get('volume_scale')) or 1
  depth=max(0,min(int(ls.get('safety_orders') or 0),int(round(n(m.get('average_safety_orders')) or 0))))
  expected_reserve+=sum(so*(vs**i) for i in range(depth))
 conditional=max(0,free-hard-expected_reserve-safety) if free is not None else None
 rows=[]
 for s in spec.get('specs') or []:
  req=n(s.get('capital_required_usdt'))
  rows.append({'asset':s.get('asset'),'capital_required_usdt':req,'fits_prudent_pool':bool(deploy is not None and req is not None and deploy>=req)})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
 'exchange_equity_usdt':equity,'free_usdt':free,'hard_exchange_commitments_usdt':round(hard,2),
 'theoretical_full_dca_reserve_usdt':round(theoretical,2),'prudent_active_dca_contingency_usdt':round(contingency,2),
 'portfolio_safety_buffer_usdt':round(safety,2),'safe_multi_bot_pool_usdt':round(deploy,2) if deploy is not None else None,
 'conditional_multi_bot_capacity_usdt':round(conditional,2) if conditional is not None else None,
 'expected_active_dca_reserve_usdt':round(expected_reserve,2),
 'conditional_capacity_is_advisory_only':True,
 'worst_case_headroom_usdt':round(max(0,(free or 0)-hard-theoretical),2) if free is not None else None,
 'candidates':rows,'read_only':True,
 'explanation':'Safe allocation remains conservative. CRM also calculates a clearly labelled conditional multi-bot capacity from validated average DCA depth, but it is advisory only and never used to unlock live deployment automatically.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f"Portfolio Capital Manager 2.0: safe_pool={p['safe_multi_bot_pool_usdt']}");return 0
if __name__=='__main__':raise SystemExit(main())
