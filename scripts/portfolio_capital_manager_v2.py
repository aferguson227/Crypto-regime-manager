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
 cap=load('capital_intelligence.json');live=load('live_portfolio_truth.json');spec=load('dca_deployment_specs.json')
 free=n(cap.get('free_available'));equity=n(cap.get('exchange_equity'));hard=n(cap.get('placed_order_reserve')) or 0
 theoretical=n(cap.get('remaining_active_deal_dca_reserve')) or n(cap.get('reserved_capital')) or 0
 # Preserve a hard worst-case figure, but use a prudent multi-bot reserve for advisory allocation.
 contingency=max(hard, theoretical*.65)
 safety=(equity*.10 if equity is not None else (free*.10 if free is not None else 0))
 deploy=max(0,free-hard-contingency-safety) if free is not None else None
 rows=[]
 for s in spec.get('specs') or []:
  req=n(s.get('capital_required_usdt'))
  rows.append({'asset':s.get('asset'),'capital_required_usdt':req,'fits_prudent_pool':bool(deploy is not None and req is not None and deploy>=req)})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
 'exchange_equity_usdt':equity,'free_usdt':free,'hard_exchange_commitments_usdt':round(hard,2),
 'theoretical_full_dca_reserve_usdt':round(theoretical,2),'prudent_active_dca_contingency_usdt':round(contingency,2),
 'portfolio_safety_buffer_usdt':round(safety,2),'safe_multi_bot_pool_usdt':round(deploy,2) if deploy is not None else None,
 'worst_case_headroom_usdt':round(max(0,(free or 0)-hard-theoretical),2) if free is not None else None,
 'candidates':rows,'read_only':True,
 'explanation':'Hard exchange commitments remain fully reserved. A separate prudent contingency reserve supports advisory multi-bot planning while worst-case DCA headroom remains visible. CRM still cannot deploy automatically.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f"Portfolio Capital Manager 2.0: safe_pool={p['safe_multi_bot_pool_usdt']}");return 0
if __name__=='__main__':raise SystemExit(main())
