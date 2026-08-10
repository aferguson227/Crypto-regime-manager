#!/usr/bin/env python3
"""V61 provider-independent DCA deployment specification.

Converts the frozen KuCoin training winner into a complete operational setup
without pretending untested fields were optimised. Research-tested fields retain
their exact winning values; execution-only fields use conservative governed
defaults and are labelled as such.

No order or bot mutation occurs.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'dca_deployment_specs.json'

def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def num(v):
 try:return float(v) if v not in (None,'') else None
 except:return None
def capital(bo,so,n,vs):
 if None in (bo,so,n,vs):return None
 return bo+sum(so*(vs**i) for i in range(int(n)))
def main():
 review=load('candidate_review.json');rows=[]
 for c in review.get('candidates') or []:
  st=dict(c.get('settings') or {});vm=c.get('validation_metrics') or {};a=c.get('asset')
  if not st:continue
  # replay/backtest engine currently validates BO=100 / SO=100. Preserve those
  # exact assumptions until sizing becomes an explicit optimisation dimension.
  bo=100.0;so=100.0;n=int(st.get('safety_orders') or 0);vs=num(st.get('volume_scale'))
  required=num(vm.get('max_capital')) or capital(bo,so,n,vs)
  trigger=c.get('entry_trigger') or 'manual'
  full={
   'base_order_volume':bo,'safety_order_volume':so,
   'take_profit_pct':st.get('take_profit_pct'),'so_deviation_pct':st.get('so_deviation_pct'),
   'safety_orders':st.get('safety_orders'),'volume_scale':st.get('volume_scale'),'step_scale':st.get('step_scale'),
   'max_active_safety_orders':min(3,n) if n else 1,'max_active_deals':1,
   'start_condition':'CRM signal / manual entry when validated trigger passes',
   'entry_trigger':trigger,'order_type':'market base order / limit DCA orders',
   'trailing_enabled':False,'cooldown_seconds':0
  }
  tested={'take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale','entry_trigger','base_order_volume','safety_order_volume'}
  sources={k:('FROZEN_BACKTEST_SETTING' if k in tested else 'GOVERNED_EXECUTION_DEFAULT') for k in full}
  missing=[k for k,v in full.items() if v is None]
  rows.append({'asset':a,'pair':c.get('pair') or f'{a}-USDT','current_regime':c.get('current_regime'),
   'setup':full,'setting_sources':sources,'setup_completeness_pct':round(100*(len(full)-len(missing))/len(full),1),'missing_settings':missing,
   'capital_required_usdt':round(required,2) if required is not None else None,
   'capital_sizing_status':'BACKTEST_ASSUMPTION' if required is not None else 'PENDING',
   'capital_sizing_explanation':'BO/SO sizes preserve the exact 100/100 USDT assumptions used by the current backtest engine. V61 does not falsely label those sizes as optimised.',
   'entry_explanation':f"Wait for the validated {trigger} entry condition; CRM does not automatically submit the entry.",
   'manual_deployment_only':True,'automatic_live_execution':False})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'specs':rows,'principle':'Research-tested values and governed execution defaults are labelled separately. Complete setup does not imply deployment approval.',
  'next_phase':'DCA Optimisation 2.0 may explicitly optimise BO/SO sizing, active-SO concurrency, entry filters and cooldown after operational truth is stable.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'DCA deployment specs written: {len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
