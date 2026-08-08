#!/usr/bin/env python3
"""V49 advisory portfolio allocation engine. Read-only; never deploys bots."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'portfolio_allocation_recommendations.json';POL=ROOT/'config'/'v49_autonomy_policy.json'
def load(p):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def main():
 cap=load(DOCS/'capital_intelligence.json');bots=load(DOCS/'recommended_bots.json');p=load(POL);policy=p.get('portfolio_policy') or {}
 deploy=num(cap.get('deployable_capital'));free=num(cap.get('free_available'))
 if deploy is None and free is not None:
  reserve=num(cap.get('remaining_active_deal_dca_reserve')) or num(cap.get('reserved_capital')) or 0
  deploy=max(0,free-reserve)
 cash_pct=float(policy.get('cash_buffer_pct',15));usable=max(0,deploy*(1-cash_pct/100)) if deploy is not None else None
 rows=[]
 ready=[x for x in bots.get('candidates') or [] if x.get('state')=='DEPLOYMENT_REVIEW_READY']
 for x in ready:
  if usable is None:amount=None;reason='Deployable KuCoin capital is not currently available.'
  else:
   pct=min(float(policy.get('pilot_allocation_pct_of_deployable',18)),float(policy.get('max_single_candidate_pct_of_deployable',25)))
   amount=round(max(float(policy.get('minimum_allocation_usdt',100)),usable*pct/100),2)
   amount=min(amount,round(usable,2))
   reason=f'{pct:.0f}% pilot share of deployable capital after {cash_pct:.0f}% cash buffer.'
  rows.append({'asset':x.get('asset'),'pair':x.get('pair'),'recommended_allocation_usdt':amount,'reason':reason,'confidence_pct':x.get('confidence_pct'),'manual_approval_required':True})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'deployable_capital_usdt':deploy,'usable_after_cash_buffer_usdt':round(usable,2) if usable is not None else None,'recommendations':rows,'automatic_deployment':False,'next_phase':'V50 may score diversification/correlation before allocation; V49 remains advisory.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print('Portfolio allocation recommendations written:',OUT);return 0
if __name__=='__main__':raise SystemExit(main())
