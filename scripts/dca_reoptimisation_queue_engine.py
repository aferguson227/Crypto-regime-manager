#!/usr/bin/env python3
"""V66 DCA re-optimisation lifecycle.

A failed unseen-validation run is complete, not "100% in progress". CRM queues a
new bounded experiment for the next research cycle after the walk-forward dataset
has advanced. It never tunes the failed winner directly against the same unseen
validation result.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'dca_reoptimisation_queue.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 opt=load('dca_optimisation_v2.json');wf=load('kucoin_walk_forward.json');wby={str(x.get('asset') or '').upper():x for x in wf.get('assets') or []}
 rows=[]
 for x in opt.get('assets') or []:
  if x.get('optimisation_status')!='UNSEEN_VALIDATION_FAILED':continue
  a=str(x.get('asset') or '').upper();w=wby.get(a) or {};period=w.get('period') or {}
  rows.append({'asset':a,'state':'QUEUED_FOR_FRESH_RESEARCH','reason':'The completed training winner failed unseen validation. CRM will run a new bounded optimisation only after the refreshed walk-forward dataset advances; it will not tune against the failed unseen result.',
   'latest_data_end':period.get('end'),'failed_settings_withheld':True,'automatic_live_changes':False})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
    'items':rows,'count':len(rows),'principle':'Validation failure causes a fresh-research queue, never leakage-driven tuning on the same unseen sample.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'DCA re-optimisation queue: {len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
