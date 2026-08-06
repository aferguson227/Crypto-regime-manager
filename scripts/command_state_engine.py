#!/usr/bin/env python3
"""V33 canonical read-only command-state synthesiser.

Combines governed market, portfolio, capital, recommendation, adaptive,
outcome and cloud evidence into one immutable advisory snapshot.
"""
from __future__ import annotations
import hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.command_state import CommandPriority, CommandState
DOCS=ROOT/'docs'; OUTPUT=DOCS/'command_state.json'

def load(name:str)->dict[str,Any]:
    try:
        value=json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
        return value if isinstance(value,dict) else {}
    except Exception:
        return {}

def number(value:Any)->float|None:
    try:
        result=float(value)
        return result if math.isfinite(result) else None
    except (TypeError,ValueError):
        return None

def build()->dict[str,Any]:
    market=load('market_intelligence.json')
    portfolio=load('portfolio_intelligence.json')
    capital=load('capital_intelligence.json')
    deployment=load('deployment_intelligence.json')
    recommendations=load('recommendation_intelligence.json')
    adaptive=load('adaptive_intelligence.json')
    outcomes=load('outcome_intelligence.json')
    cloud=load('cloud_reliability.json')
    three=load('threecommas.json')
    diagnostics=load('diagnostics.json')
    operating=load('operating_state.json')
    generated=datetime.now(timezone.utc).isoformat()

    recs=[]; queue=[]; risks=[]; warnings=[]
    adaptive_rows={str(r.get('asset')):r for r in adaptive.get('strategies') or [] if isinstance(r,dict)}
    for rec in recommendations.get('recommendations') or []:
        if not isinstance(rec,dict): continue
        asset=str(rec.get('asset') or 'UNKNOWN'); action=str(rec.get('action') or 'WAIT')
        adaptive_row=adaptive_rows.get(asset,{})
        confidence=number(adaptive_row.get('effective_score')) or number(rec.get('overall_confidence'))
        blockers=tuple(str(x) for x in rec.get('blockers') or [])
        supports=tuple(str(x) for x in rec.get('supporting_evidence') or [])
        capital_impact=rec.get('capital_impact') or {}
        urgency='NOW' if action=='DEPLOY_TODAY' and not blockers else ('MONITOR' if action=='KEEP_RUNNING' else 'WAIT')
        recs.append({
            'recommendation_id':rec.get('recommendation_id'),'asset':asset,'bot_name':rec.get('bot_name'),
            'action':action,'confidence_pct':confidence,'static_confidence_pct':rec.get('overall_confidence'),
            'adaptive_active':bool(adaptive_row.get('adaptive_active')),'risk_level':rec.get('risk_level'),
            'explanation':rec.get('explanation'),'supporting_evidence':list(supports),'risks':rec.get('risks') or [],
            'blockers':list(blockers),'production_comparison':rec.get('production_comparison') or {},
            'capital_impact':capital_impact,'expected_behaviour':rec.get('expected_behaviour') or {},
            'evidence_agreement':rec.get('evidence_agreement') or {},
        })
        queue.append(CommandPriority(
            rank=0,category='deployment',asset=asset,bot_name=rec.get('bot_name'),action=action,
            confidence_pct=confidence,urgency=urgency,rationale=supports[:4],blockers=blockers[:4],
            capital_required=number(capital_impact.get('required')),can_fund=capital_impact.get('can_fund')
        ))
        risks.extend(str(x) for x in rec.get('risks') or [])
        risks.extend(f'{asset}: {x}' for x in blockers)

    def priority(item:CommandPriority)->tuple[int,float]:
        action_order={'DEPLOY_TODAY':0,'KEEP_RUNNING':1,'WAIT':2}
        blocked=1 if item.blockers else 0
        return (blocked*10+action_order.get(item.action,9),-(item.confidence_pct or 0))
    ordered=[]
    for idx,item in enumerate(sorted(queue,key=priority),1):
        ordered.append(CommandPriority(idx,item.category,item.asset,item.bot_name,item.action,item.confidence_pct,item.urgency,item.rationale,item.blockers,item.capital_required,item.can_fund))

    market_summary={
        'regime':market.get('regime') or operating.get('current_market_regime') or 'Unknown',
        'confidence_pct':market.get('regime_confidence_pct'),'risk_appetite':market.get('risk_appetite'),
        'recommended_exposure':market.get('recommended_exposure'),'trend_score':market.get('trend_score'),
        'breadth_score':market.get('breadth_score'),'volatility_score':market.get('volatility_score'),
        'stress_tests':market.get('stress_tests') or [],
    }
    portfolio_summary={
        'health_score':portfolio.get('portfolio_health_score'),'diversification_score':portfolio.get('diversification_score'),
        'capital_efficiency_score':portfolio.get('capital_efficiency_score'),'next_capital_priority':portfolio.get('next_capital_priority'),
        'positions':portfolio.get('positions') or [],'overlap_analysis':portfolio.get('overlap_analysis') or {},
    }
    capital_summary={
        'status':capital.get('status'),'currency':capital.get('currency') or portfolio.get('currency') or 'USDT',
        'total_equity':portfolio.get('total_equity') or capital.get('exchange_total'),
        'allocated':portfolio.get('allocated_capital') or capital.get('active_deal_capital'),
        'reserved':portfolio.get('reserved_capital') or capital.get('reserved_capital'),
        'deployable':portfolio.get('deployable_capital') or capital.get('deployable_capital'),
        'next_required':capital.get('next_priority_required_capital'),'can_fund_next':capital.get('can_fund_next_priority'),
        'asset_allocations':capital.get('asset_allocations') or [],
    }
    cloud_summary={
        'overall_status':cloud.get('overall_status') or cloud.get('status') or 'UNKNOWN',
        'threecommas':cloud.get('threecommas') or {'status':three.get('status'),'generated_at':three.get('generated_at'),'message':three.get('message')},
        'main_app':cloud.get('main_app') or {},'publication':cloud.get('publication') or {},
    }
    diag_overall=diagnostics.get('overall') or {}
    health={'diagnostics_state':diag_overall.get('state'),'diagnostics_score':diag_overall.get('score'),
            'threecommas_read_only':three.get('read_only',True),'cloud_status':cloud_summary['overall_status']}
    outcome_summary={'completed':(outcomes.get('summary') or {}).get('completed'),'accuracy_pct':(outcomes.get('summary') or {}).get('accuracy_pct'),
                     'average_return_pct':(outcomes.get('summary') or {}).get('average_realised_return_pct')}
    evidence={'adaptive':{'active_count':sum(1 for x in adaptive_rows.values() if x.get('adaptive_active')),
                          'minimum_evidence':adaptive.get('minimum_evidence')},
              'outcomes':outcome_summary,'cross_source':deployment.get('evidence_summary') or {},
              'market_attribution':market.get('confidence_attribution') or {}}
    warnings.extend(str(x) for x in market.get('warnings') or [])
    warnings.extend(str(x) for x in portfolio.get('warnings') or [])
    warnings.extend(str(x) for x in capital.get('warnings') or [])
    warnings.extend(str(x) for x in recommendations.get('warnings') or [])
    if capital_summary['deployable'] is None: warnings.append('Deployable capital is unknown; no new deployment should be assumed fundable.')
    if str(cloud_summary['overall_status']).upper() not in {'HEALTHY','OK','PASS'}: warnings.append('One or more cloud data sources require attention.')
    overall='READY'
    if any(q.action=='DEPLOY_TODAY' and not q.blockers and q.can_fund is True for q in ordered): overall='ACTION_AVAILABLE'
    elif any(q.action=='KEEP_RUNNING' for q in ordered): overall='MAINTAIN'
    if str(diag_overall.get('state')).lower()=='fail': overall='SYSTEM_ATTENTION'
    sources={name:(obj.get('snapshot_id') or obj.get('generated_at')) for name,obj in {
        'market':market,'portfolio':portfolio,'capital':capital,'deployment':deployment,'recommendations':recommendations,
        'adaptive':adaptive,'outcomes':outcomes,'cloud':cloud,'operating':operating}.items()}
    seed=json.dumps({'overall':overall,'market':market_summary,'capital':capital_summary,'queue':[q.__dict__ for q in ordered],'sources':sources},sort_keys=True,default=str)
    payload=CommandState('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:24],
        'unified_read_only_trading_command_state',True,True,overall,market_summary,portfolio_summary,capital_summary,
        tuple(recs),tuple(ordered),tuple(dict.fromkeys(risks)),evidence,cloud_summary,health,sources,tuple(dict.fromkeys(warnings))).to_dict()
    return payload

def main()->int:
    payload=build(); OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(f'Command state written: {OUTPUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
