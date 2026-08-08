#!/usr/bin/env python3
"""V45 governed optimisation queue.
A candidate is not a deployment candidate until the current-regime research stage
is complete and independent historical validation remains positive.
"""
from __future__ import annotations
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'optimisation_queue.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return v if isinstance(v,dict) else {}
 except:return {}
def main():
 pipe=load('research_pipeline.json');globalm=load('global_market.json');research=load('regime_backtest_intelligence.json');kuwf=load('kucoin_walk_forward.json');current=str(globalm.get('regime') or 'UNKNOWN')
 family='BULL' if current in {'BULL','STRONG_BULL'} else ('BEAR' if current in {'BEAR','DISTRIBUTION','CAPITULATION'} else current)
 byasset={str(x.get('asset') or '').upper():x for x in research.get('datasets') or [] if isinstance(x,dict)}
 kuby={str(x.get('asset') or '').upper():x for x in kuwf.get('assets') or [] if isinstance(x,dict)}
 rows=[]
 for c in pipe.get('candidates') or []:
  if not isinstance(c,dict):continue
  asset=str(c.get('asset') or '').upper();base=c.get('frozen_settings') or {};stage=c.get('stage');rr=byasset.get(asset) or {};profile=(rr.get('regime_profiles') or {}).get(family);kw=kuby.get(asset) or {};kp=(kw.get('current_regime_profile') or {})
  independent_pass=stage=='READY_FOR_MANUAL_REVIEW' and str(c.get('walk_forward_status') or '').upper()=='PASS'
  kucoin_pass=bool(kw.get('kucoin_primary_validation_pass'))
  if kucoin_pass:
   status='KUCOIN_WALK_FORWARD_COMPLETE'
   frozen=(kp.get('frozen_training_winner') or {})
   profile={'entry_trigger':frozen.get('entry_trigger'),'settings':frozen.get('settings'),'metrics':kp.get('validation_metrics'),'trade_fluidity':'GOOD' if (kp.get('validation_metrics') or {}).get('longest_hours',9999)<=168 else 'CAUTION','status':'EXPLORATORY_PASS'}
  elif independent_pass and profile and profile.get('status')=='EXPLORATORY_PASS':status='REGIME_RESEARCH_COMPLETE'
  elif independent_pass:status='INDEPENDENT_BASELINE_PASS_REGIME_RESEARCH_PENDING'
  elif stage=='RESEARCH_REJECT':status='REJECTED'
  else:status='WAIT'
  profile_settings=(profile or {}).get('settings') or None
  recommended=profile_settings if status in {'REGIME_RESEARCH_COMPLETE','KUCOIN_WALK_FORWARD_COMPLETE'} else (base or None)
  rows.append({'asset':asset,'pair':c.get('pair'),'status':status,'current_global_regime':current,'current_regime_family':family,'validated_baseline':base or None,
    'current_regime_profile':profile,'recommended_research_settings':recommended,'independent_validation_status':c.get('walk_forward_status'),
    'deployment_candidate':status in {'REGIME_RESEARCH_COMPLETE','KUCOIN_WALK_FORWARD_COMPLETE'},'manual_approval_required':True,'automatic_live_changes':False,
    'kucoin_walk_forward_status':kw.get('status'),'kucoin_validation':kp.get('validation_metrics'),'next_action':('Review KuCoin-frozen current-regime settings and evidence; manual deployment only.' if status=='KUCOIN_WALK_FORWARD_COMPLETE' else ('Review current-regime settings and evidence; manual deployment only.' if status=='REGIME_RESEARCH_COMPLETE' else ('Background regime research requires a comparable 4h dataset for this asset.' if independent_pass else 'Remain in research queue.')))})
 payload={'schema_version':'1.1','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'current_global_regime':current,'current_regime_family':family,'items':rows,
  'process':['DISCOVERY','ENTRY_TRIGGER_RESEARCH','DCA_OPTIMISATION','TRADE_FLUIDITY_REVIEW','FREEZE_TRAINING_SETTINGS','INDEPENDENT_VALIDATION','CURRENT_REGIME_CONFIRMATION','MANUAL_DEPLOYMENT_REVIEW'],
  'automatic_queue_management':True,'automatic_backtesting':True,'automatic_live_deployment':False,'manual_approval_required':True}
 payload['snapshot_id']=hashlib.sha256(json.dumps([(x['asset'],x['status'],x.get('current_regime_family')) for x in rows],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Optimisation queue written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
