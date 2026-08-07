#!/usr/bin/env python3
"""V42 governed research-promotion engine.

Combines current KuCoin candidate discovery with the frozen Kraken/Q1 registry.
It may advance research *state* to manual review, but never changes production,
bots, settings, orders or exchange state.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'research_pipeline.json'

def load(name):
    try:
        v=json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
        return v if isinstance(v,dict) else {}
    except Exception:return {}

def build():
    discovery=load('coin_discovery.json'); registry=load('walk_forward_registry.json')
    reg={str(x.get('symbol') or '').upper():x for x in registry.get('coins') or [] if isinstance(x,dict)}
    candidates=discovery.get('researched_candidates') or discovery.get('candidates') or []
    rows=[]
    for c in candidates[:20]:
        if not isinstance(c,dict): continue
        pair=str(c.get('symbol') or '')
        asset=str(c.get('base_currency') or pair.split('-')[0]).upper()
        wf=reg.get(asset)
        status=str((wf or {}).get('status') or 'MISSING').upper()
        q=(wf or {}).get('q1_2026_metrics') or {}
        training=(wf or {}).get('training_metrics') or {}
        current_score=c.get('research_score')
        gates={
          'current_kucoin_screen':'PASS' if c.get('eligible',True) else 'FAIL',
          'kraken_training':'PASS' if wf and training else 'MISSING',
          'q1_independent_validation':'PASS' if status=='PASS' and q else ('FAIL' if wf else 'MISSING'),
          'drawdown_review':'REVIEW' if wf else 'MISSING',
          'manual_approval':'REQUIRED',
        }
        if status=='PASS' and c.get('eligible',True):
            stage='READY_FOR_MANUAL_REVIEW'
        elif wf and status=='FAIL':
            stage='RESEARCH_REJECT'
        else:
            stage='NEEDS_HISTORICAL_VALIDATION'
        rows.append({
          'asset':asset,'pair':pair,'discovery_rank':c.get('rank'),'current_research_score':current_score,
          'stage':stage,'walk_forward_status':status if wf else None,'frozen_settings':(wf or {}).get('frozen_settings'),
          'training_metrics':training or None,'q1_2026_metrics':q or None,'gates':gates,
          'production_eligible':False,'manual_approval_required':True,'automatic_promotion':False,
          'next_action':(
            'Review frozen Kraken/Q1 evidence against current KuCoin conditions; manual approval only.'
            if stage=='READY_FOR_MANUAL_REVIEW' else
            'Retain as research-only; historical validation failed.' if stage=='RESEARCH_REJECT' else
            'Acquire/import comparable historical data and run frozen walk-forward validation.'
          )
        })
    ready=sum(1 for x in rows if x['stage']=='READY_FOR_MANUAL_REVIEW')
    missing=sum(1 for x in rows if x['stage']=='NEEDS_HISTORICAL_VALIDATION')
    rejected=sum(1 for x in rows if x['stage']=='RESEARCH_REJECT')
    payload={
      'schema_version':'1.0','application_version':application_version(),
      'generated_at':datetime.now(timezone.utc).isoformat(),
      'mode':'governed_read_only_research_promotion',
      'automatic_backtest_execution':False,'automatic_production_promotion':False,
      'manual_approval_required':True,
      'summary':{'candidate_count':len(rows),'ready_for_manual_review':ready,'needs_historical_validation':missing,'research_reject':rejected},
      'candidates':rows,
      'policy':{
        'production_requires':['current KuCoin screen','frozen historical training','independent Q1 validation','drawdown review','manual approval'],
        'no_data_no_claim':True,'no_automatic_bot_changes':True
      }
    }
    payload['snapshot_id']=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:24]
    return payload

def main():
    OUT.write_text(json.dumps(build(),indent=2),encoding='utf-8')
    print(f'Research pipeline written: {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
