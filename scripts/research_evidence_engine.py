#!/usr/bin/env python3
"""V41.2 research evidence bridge.

Maps current discovery candidates onto the frozen Kraken/Q1 walk-forward registry.
It never promotes a coin to production automatically; missing archive evidence is
reported explicitly for the next research cycle.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'research_evidence.json'

def load(name):
    try:
        d=json.loads((DOCS/name).read_text(encoding='utf-8-sig')); return d if isinstance(d,dict) else {}
    except Exception:return {}

def main():
    cand=load('candidate_validation.json'); walk=load('walk_forward_registry.json')
    registry={str(x.get('symbol') or '').upper():x for x in walk.get('coins') or [] if isinstance(x,dict)}
    rows=[]
    for c in cand.get('candidates') or []:
        if not isinstance(c,dict): continue
        pair=str(c.get('symbol') or ''); asset=pair.split('-')[0].upper(); w=registry.get(asset)
        if w:
            status='VALIDATED_PASS' if str(w.get('status')).upper()=='PASS' else 'VALIDATED_FAIL'
            next_action='Current frozen Kraken/Q1 result may inform evidence scoring; manual approval remains required.' if status=='VALIDATED_PASS' else 'Keep as research/reject unless a new independent validation cycle is explicitly approved.'
        else:
            status='NEEDS_KRAKEN_VALIDATION'; next_action='Acquire/import comparable historical and independent validation data before production consideration.'
        rows.append({'asset':asset,'pair':pair,'discovery_rank':c.get('discovery_rank'),'research_score':c.get('research_score'),'candidate_stage':c.get('stage'),'kraken_validation_status':status,'walk_forward_status':w.get('status') if w else None,'training_metrics':w.get('training_metrics') if w else None,'q1_2026_metrics':w.get('q1_2026_metrics') if w else None,'frozen_settings':w.get('frozen_settings') if w else None,'automatic_promotion':False,'manual_approval_required':True,'next_action':next_action})
    passed=sum(1 for x in rows if x['kraken_validation_status']=='VALIDATED_PASS'); covered=sum(1 for x in rows if x['walk_forward_status'] is not None)
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'read_only_research_evidence_bridge','automatic_forward_testing':False,'automatic_production_promotion':False,'manual_approval_required':True,'candidate_count':len(rows),'kraken_registry_coverage_count':covered,'validated_pass_count':passed,'coverage_pct':round(100*covered/len(rows),1) if rows else None,'candidates':rows,'next_phase':'Automate fee-aware replay and independent forward validation only when comparable local research archives are available.'}
    payload['snapshot_id']=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:20]
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Research evidence written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
