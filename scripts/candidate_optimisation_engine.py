#!/usr/bin/env python3
"""V44 candidate optimisation queue.
Creates regime-aware optimisation work items. Existing Kraken/Q1 frozen settings
are retained as validated baselines. Fresh multi-regime backtests only become
RUNNABLE when comparable raw research archives are configured locally.
"""
from __future__ import annotations
import json,hashlib,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'optimisation_queue.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
 except:return {}
def main():
 pipe=load('research_pipeline.json'); globalm=load('global_market.json'); current=globalm.get('regime') or 'UNKNOWN'
 training=Path(os.getenv('CRM_KRAKEN_TRAINING_DIR',r'C:\Crypto\Research\Kraken\training'))
 validation=Path(os.getenv('CRM_KRAKEN_VALIDATION_DIR',r'C:\Crypto\Research\Kraken\validation'))
 raw_ready=training.exists() and validation.exists()
 rows=[]
 for c in pipe.get('candidates') or []:
  if not isinstance(c,dict):continue
  base=c.get('frozen_settings') or {}
  stage=c.get('stage')
  status='RUNNABLE' if raw_ready and stage=='READY_FOR_MANUAL_REVIEW' else ('VALIDATED_BASELINE' if stage=='READY_FOR_MANUAL_REVIEW' else 'WAIT')
  rows.append({'asset':c.get('asset'),'pair':c.get('pair'),'status':status,'current_global_regime':current,'validated_baseline':base or None,
    'regime_profiles':{'BULL':{'status':'PENDING_OPTIMISATION'},'ACCUMULATION':{'status':'PENDING_OPTIMISATION'},'NEUTRAL':{'status':'PENDING_OPTIMISATION'},'BEAR':{'status':'PENDING_OPTIMISATION'}},
    'raw_archives_available':raw_ready,'next_action':('Run fee-aware multi-regime optimisation against configured Kraken training/validation archives.' if status=='RUNNABLE' else ('Use frozen Kraken/Q1 baseline while retaining manual approval; raw archives are required for a fresh regime optimisation.' if status=='VALIDATED_BASELINE' else 'Remain in research queue.')),
    'automatic_live_changes':False})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'current_global_regime':current,'raw_archive_paths':{'training':str(training),'validation':str(validation),'available':raw_ready},'items':rows,'automatic_queue_management':True,'automatic_live_deployment':False,'manual_approval_required':True}
 payload['snapshot_id']=hashlib.sha256(json.dumps([(x['asset'],x['status']) for x in rows],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Optimisation queue written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
