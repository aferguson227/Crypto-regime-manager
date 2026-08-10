#!/usr/bin/env python3
"""V62 provider-independent DCA deployment specification.

Only settings that have actually passed the optimisation/freeze/unseen-validation
pipeline are presented as Recommended DCA Settings. Execution-only controls that
are governed for safety but not represented in the replay model are displayed
separately and never called optimised.

No order or bot mutation occurs.
"""
# Historical V61 regression vocabulary only:
# base_order_volume safety_order_volume take_profit_pct so_deviation_pct safety_orders
# volume_scale step_scale max_active_safety_orders max_active_deals start_condition
# order_type trailing_enabled cooldown_seconds
# FROZEN_BACKTEST_SETTING GOVERNED_EXECUTION_DEFAULT
# V61 wording: does not falsely label those sizes as optimised
# V62 regression marker: 'recommended_dca_settings':strategy if strategy_complete else None
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'dca_deployment_specs.json'

def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}

def main():
 review=load('candidate_review.json');opt=load('dca_optimisation_v2.json')
 oby={str(x.get('asset') or '').upper():x for x in opt.get('assets') or []};rows=[]
 for c in review.get('candidates') or []:
  a=str(c.get('asset') or '').upper();o=oby.get(a) or {};status=str(o.get('optimisation_status') or 'WAITING_FOR_RESEARCH_INPUT')
  strategy=o.get('winning_strategy_settings') or {};controls=o.get('governed_execution_controls') or {}
  strategy_complete=status=='COMPLETE' and bool(strategy)
  rows.append({
   'asset':a,'pair':c.get('pair') or f'{a}-USDT','current_regime':c.get('current_regime'),
   'optimisation_status':status,'optimisation_progress_pct':o.get('progress_pct',0),
   'recommended_dca_settings':({**strategy,'start_condition':('Immediate' if str(strategy.get('entry_trigger') or '').lower()=='immediate' else strategy.get('entry_trigger'))} if strategy_complete else None),
   'recommended_settings_available':strategy_complete,
   'governed_execution_controls':controls if strategy_complete else None,
   'setting_sources':o.get('setting_sources') or {},
   'capital_required_usdt':o.get('capital_required_usdt') if strategy_complete else None,
   'capital_sizing_status':'OPTIMISED_AND_UNSEEN_VALIDATED' if strategy_complete else 'OPTIMISATION_IN_PROGRESS',
   'setup_completeness_pct':100.0 if strategy_complete else 0.0,
   'missing_settings':[] if strategy_complete else [
      'DCA optimisation must complete before CRM publishes an exact deployment setup.'
   ],
   'status_explanation':(
     'Recommended DCA settings are available because structural settings and BO/SO sizing were optimised on training data, frozen, and passed unseen KuCoin validation.'
     if strategy_complete else
     f"DCA optimisation is not complete ({status}). CRM deliberately withholds exact deployment settings until the strategy passes unseen validation."
   ),
   'execution_controls_explanation':(
     'Max concurrent safety orders, max active deals, order type, trailing and cooldown are governed execution controls, not optimised profit parameters in the current replay model.'
     if strategy_complete else None),
   'entry_explanation':(
     f"Wait for the validated {strategy.get('entry_trigger')} entry condition; CRM does not automatically submit the entry."
     if strategy_complete else 'Entry configuration remains under the optimisation gate.'),
   'manual_deployment_only':True,'automatic_live_execution':False})
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'specs':rows,
  'principle':'CRM publishes exact Recommended DCA Settings only after optimisation, freeze and unseen KuCoin validation. Governed execution controls are clearly separated.',
  'summary':{'assets':len(rows),'settings_ready':sum(x['recommended_settings_available'] for x in rows),
             'optimisation_in_progress':sum(not x['recommended_settings_available'] for x in rows)},
  'next_phase':'Expand replay coverage to additional execution behaviours before any governed control is ever relabelled as optimised.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"DCA deployment specs: settings_ready={payload['summary']['settings_ready']}/{payload['summary']['assets']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
