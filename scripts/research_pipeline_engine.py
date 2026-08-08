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
    discovery=load('coin_discovery.json'); registry=load('walk_forward_registry.json'); kuwf=load('kucoin_walk_forward.json')
    reg={str(x.get('symbol') or '').upper():x for x in registry.get('coins') or [] if isinstance(x,dict)}
    candidates=[];seen=set()
    for c in (discovery.get('researched_candidates') or [])+(discovery.get('shortlist') or [])+(discovery.get('candidates') or []):
        if not isinstance(c,dict):continue
        pair=str(c.get('symbol') or '')
        if pair and pair not in seen:seen.add(pair);candidates.append(c)
    ku={str(x.get('asset') or '').upper():x for x in kuwf.get('assets') or [] if isinstance(x,dict)}
    rows=[]
    for c in candidates[:20]:
        if not isinstance(c,dict): continue
        pair=str(c.get('symbol') or '')
        asset=str(c.get('base_currency') or pair.split('-')[0]).upper()
        wf=reg.get(asset); kw=ku.get(asset)
        status=str((wf or {}).get('status') or 'MISSING').upper(); kstatus=str((kw or {}).get('status') or 'MISSING').upper()
        q=(wf or {}).get('q1_2026_metrics') or {}
        training=(wf or {}).get('training_metrics') or {}
        current_score=c.get('research_score')
        gates={
          'current_kucoin_screen':'PASS' if c.get('eligible',True) else 'FAIL',
          'kucoin_history':'PASS' if kw and (kw.get('bars') or 0)>0 else 'BUILDING',
          'kucoin_walk_forward':'PASS' if kstatus=='READY_FOR_MANUAL_REVIEW' else ('FAIL' if kw and kw.get('deployment_gate')=='FAIL' else 'PENDING'),
          'kraken_robustness':'PASS' if status=='PASS' else ('FAIL' if wf and status=='FAIL' else 'OPTIONAL'),
          'drawdown_review':'REVIEW' if (kw or wf) else 'PENDING',
          'manual_approval':'REQUIRED',
        }
        if kstatus=='READY_FOR_MANUAL_REVIEW' and c.get('eligible',True):
            stage='READY_FOR_MANUAL_REVIEW'
        elif status=='PASS' and c.get('eligible',True) and not kw:
            stage='READY_FOR_MANUAL_REVIEW'
        elif kw and kw.get('deployment_gate')=='FAIL':
            stage='RESEARCH_REJECT'
        elif wf and status=='FAIL' and not kw:
            stage='RESEARCH_REJECT'
        else:
            stage='NEEDS_HISTORICAL_VALIDATION'
        rows.append({
          'asset':asset,'pair':pair,'discovery_rank':c.get('rank'),'current_research_score':current_score,
          'stage':stage,'walk_forward_status':status if wf else None,'kucoin_walk_forward_status':kstatus if kw else None,'kucoin_primary_validation_pass':bool((kw or {}).get('kucoin_primary_validation_pass')),'frozen_settings':((kw or {}).get('current_regime_profile') or {}).get('frozen_training_winner',{}).get('settings') or (wf or {}).get('frozen_settings'),
          'training_metrics':training or None,'q1_2026_metrics':q or None,'gates':gates,
          'production_eligible':False,'manual_approval_required':True,'automatic_promotion':False,
          'next_action':(
            'Review frozen KuCoin walk-forward evidence against current conditions; Kraken is secondary robustness evidence. Manual approval only.'
            if stage=='READY_FOR_MANUAL_REVIEW' else
            'Retain as research-only; historical validation failed.' if stage=='RESEARCH_REJECT' else
            'Continue automatic KuCoin history acquisition, entry/DCA optimisation and frozen walk-forward validation.'
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
        'production_requires':['current KuCoin screen','KuCoin historical training','frozen unseen KuCoin validation','drawdown/trade-fluidity review','manual approval'],
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
