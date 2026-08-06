#!/usr/bin/env python3
"""V32.8 advisory adaptive scoring and portfolio optimisation.

The static recommendation remains authoritative until sufficient completed and
judged outcomes exist. Adaptive influence is capped and never changes live bots,
production settings or orders.
"""
from __future__ import annotations
import hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.adaptive_intelligence import AdaptiveIntelligence, AdaptiveStrategy
DOCS=ROOT/'docs'; OUTPUT=DOCS/'adaptive_intelligence.json'
MIN_EVIDENCE=8; MAX_INFLUENCE=.25

def load(name:str)->dict[str,Any]:
    try:
        x=json.loads((DOCS/name).read_text(encoding='utf-8-sig')); return x if isinstance(x,dict) else {}
    except Exception:return {}
def num(v):
    try:
        f=float(v); return f if math.isfinite(f) else None
    except (TypeError,ValueError):return None
def clamp(v:float)->float:return round(max(0,min(100,v)),1)

def asset_metrics(outcome:dict[str,Any],asset:str)->dict[str,Any]:
    return ((outcome.get('analytics') or {}).get('by_asset') or {}).get(asset,{}) or {}

def calibration_for(outcome:dict[str,Any],score:float)->dict[str,Any]:
    for row in outcome.get('confidence_calibration') or []:
        band=str(row.get('band') or '')
        try:
            lo,hi=[float(x.replace('%','')) for x in band.split('-')]
            if lo<=score<hi or (score==100 and hi==100): return row
        except Exception: pass
    return {}

def build()->dict[str,Any]:
    rec=load('recommendation_intelligence.json'); outcome=load('outcome_intelligence.json'); port=load('portfolio_intelligence.json')
    generated=datetime.now(timezone.utc).isoformat(); rows=[]; warnings=[]
    positions={str(x.get('asset')):x for x in port.get('positions',[]) if isinstance(x,dict)}
    for item in rec.get('recommendations',[]) if isinstance(rec.get('recommendations'),list) else []:
        asset=str(item.get('asset') or 'UNKNOWN'); static=clamp(num(item.get('overall_confidence')) or 0)
        metrics=asset_metrics(outcome,asset); evidence=int(metrics.get('judged') or 0); accuracy=num(metrics.get('accuracy_pct')); avg_return=num(metrics.get('average_return_pct'))
        cal=calibration_for(outcome,static); observed=num(cal.get('observed_accuracy_pct'))
        position=positions.get(asset,{}) or {}; efficiency=num(position.get('efficiency_score'))
        reasons=[]; row_warnings=[]; adjustments={}
        adaptive=static; status='INSUFFICIENT_EVIDENCE'
        if evidence>=MIN_EVIDENCE and accuracy is not None:
            status='ACTIVE_CAPPED'
            accuracy_delta=max(-20,min(20,accuracy-static)); adjustments['outcome_accuracy']=round(accuracy_delta*.55,2)
            return_bonus=max(-10,min(10,(avg_return or 0)*2)); adjustments['realised_return']=round(return_bonus*.25,2)
            calibration_delta=max(-10,min(10,(observed-static) if observed is not None else 0)); adjustments['confidence_calibration']=round(calibration_delta*.20,2)
            raw=static+sum(adjustments.values()); low=static*(1-MAX_INFLUENCE); high=static+(100-static)*MAX_INFLUENCE
            adaptive=clamp(max(low,min(high,raw)))
            reasons.append(f'Adaptive score uses {evidence} judged outcomes with {accuracy:.1f}% observed accuracy.')
        else:
            row_warnings.append(f'Adaptive influence disabled until at least {MIN_EVIDENCE} judged outcomes exist for {asset}.')
            reasons.append('Static governed recommendation remains authoritative.')
        risk_adjusted=clamp(adaptive-((100-(efficiency or 50))*.10)) if efficiency is not None else adaptive
        rows.append({'asset':asset,'bot_name':str(item.get('bot_name') or asset),'action':str(item.get('action') or 'WAIT'),'static_score':static,'adaptive_score':adaptive,'effective_score':adaptive if status=='ACTIVE_CAPPED' else static,'evidence_count':evidence,'adaptation_status':status,'confidence_calibration_pct':observed,'observed_accuracy_pct':accuracy,'average_return_pct':avg_return,'capital_efficiency_score':efficiency,'risk_adjusted_score':risk_adjusted,'weight_adjustments':adjustments,'reasons':tuple(reasons),'warnings':tuple(row_warnings)})
    ranked=sorted(rows,key=lambda r:(r['risk_adjusted_score'],r['effective_score']),reverse=True)
    strategies=[]
    for rank,r in enumerate(ranked,1): strategies.append(AdaptiveStrategy(rank=rank,**r))
    deployable=num(port.get('deployable_capital')); candidate=next((s for s in strategies if s.action in {'DEPLOY_TODAY','KEEP_RUNNING'}),None)
    next_priority=candidate.bot_name if candidate else port.get('next_capital_priority')
    adaptation_enabled=any(s.adaptation_status=='ACTIVE_CAPPED' for s in strategies)
    if not adaptation_enabled:warnings.append(f'Adaptive weighting is dormant because no strategy has {MIN_EVIDENCE} judged outcomes. Static scores remain authoritative.')
    if deployable is None:warnings.append('Deployable capital is unknown; portfolio optimisation remains advisory.')
    optimisation={'recommended_next_allocation':next_priority,'deployable_capital':deployable,'weakest_strategy':strategies[-1].bot_name if strategies else None,'ranking_basis':'risk-adjusted adaptive score with capped historical influence','automatic_execution':False}
    source={'recommendation_intelligence':'recommendation_intelligence.json','outcome_intelligence':'outcome_intelligence.json','portfolio_intelligence':'portfolio_intelligence.json'}
    seed=json.dumps({'source':source,'strategies':[(s.asset,s.effective_score,s.evidence_count) for s in strategies]},sort_keys=True)
    payload=AdaptiveIntelligence('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:20],'advisory_capped_adaptive_intelligence',True,True,MIN_EVIDENCE,MAX_INFLUENCE*100,adaptation_enabled,next_priority,tuple(strategies),tuple(outcome.get('confidence_calibration') or ()),optimisation,source,tuple(warnings)).to_dict()
    return payload

def main()->int:
    p=build();OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Adaptive intelligence written: {OUTPUT}');return 0
if __name__=='__main__':raise SystemExit(main())
