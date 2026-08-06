#!/usr/bin/env python3
"""V32.5 confidence-weighted, transparent recommendation intelligence.

This module is advisory and read-only. It never changes a bot, deal, order,
setting, balance or production configuration.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.recommendation_intelligence import ConfidenceComponent, RecommendationIntelligence, RecommendationRecord
DOCS=ROOT/'docs'; OUTPUT=DOCS/'recommendation_intelligence.json'; HISTORY=DOCS/'recommendation_history.json'


def load(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding='utf-8-sig'))
        return value if isinstance(value,dict) else {}
    except Exception:return {}

def clamp(v:float)->float:return round(max(0.0,min(100.0,v)),1)

def agreement_score(e:dict[str,Any])->tuple[float|None,str,str]:
    agreement=str(e.get('agreement') or 'UNKNOWN').upper()
    if agreement=='AGREE': return 100.0,'pass','Kraken historical evidence, Q1 validation and current KuCoin conditions agree.'
    if agreement=='DISAGREE': return 20.0,'fail','The three evidence layers explicitly disagree.'
    return None,'unknown','Cross-source agreement is incomplete or unavailable.'

def capital_score(action:dict[str,Any],capital_status:str)->tuple[float|None,str,str]:
    if action.get('action')=='KEEP_RUNNING':
        return (90.0 if capital_status=='COMPLETE' else 65.0),'pass' if capital_status=='COMPLETE' else 'partial','Existing live bot can remain running, but reserve confidence follows capital completeness.'
    can=action.get('can_fund')
    if can is True:return 100.0,'pass','Deployable capital is confirmed sufficient for the next deal.'
    if can is False:return 0.0,'fail','Confirmed deployable capital is insufficient.'
    return None,'unknown','Deployable capital cannot yet be confirmed.'

def settings_score(action:dict[str,Any])->tuple[float|None,str,str]:
    s=action.get('recommended_settings') or {}
    if not s.get('complete'): return 25.0,'fail','One or more exact DCA settings are missing.'
    changed=action.get('settings_changed')
    if changed is False:return 100.0,'pass','The recommendation matches the governed production setting set.'
    if changed is True:return 70.0,'review','The recommendation differs from the live or production configuration and requires manual review.'
    return 85.0,'partial','Exact settings are complete, but a full comparison is unavailable.'

def live_score(action:dict[str,Any])->tuple[float|None,str,str]:
    state=str(action.get('live_state') or 'UNKNOWN').upper()
    if action.get('action')=='KEEP_RUNNING' and state=='RUNNING':return 100.0,'pass','The recommended bot is already running.'
    if state in {'STOPPED','DISABLED','IDLE'}:return 80.0,'pass','The bot is not currently consuming an active-deal slot.'
    if state=='RUNNING':return 70.0,'review','A live bot already exists; avoid duplicate deployment without manual review.'
    return None,'unknown','Live 3Commas state is unavailable.'

def regime_score(action:dict[str,Any])->tuple[float,str,str]:
    base=float(action.get('confidence') or 0)
    if action.get('eligible'):return clamp(max(65,base)), 'pass','Current regime and entry permission support this action.'
    return clamp(min(55,base)), 'fail','Current regime or entry permission does not support a new entry.'

def historical_score(asset:str,decisions:dict[str,Any])->tuple[float|None,str,str,dict[str,Any]]:
    row=next((r for r in decisions.get('production_ranking') or [] if r.get('id')==asset),{})
    if not row:return None,'unknown','No decision-engine historical score is available.',{}
    score=clamp(float(row.get('decision_score') or 0))
    return score,'pass' if score>=60 else 'review','Historical/replay decision score from the governed production ranking.',row

def weighted(components:list[ConfidenceComponent])->float:
    available=[c for c in components if c.score is not None and c.weight>0]
    if not available:return 0.0
    return clamp(sum(float(c.score)*c.weight for c in available)/sum(c.weight for c in available))

def risk_level(action:dict[str,Any],overall:float,evidence:dict[str,Any])->str:
    if action.get('blocking_reasons') or str(evidence.get('agreement')).upper()=='DISAGREE':return 'HIGH'
    if overall>=85 and not action.get('cautions'):return 'LOW'
    if overall>=65:return 'MODERATE'
    return 'HIGH'

def expected(row:dict[str,Any])->dict[str,Any]:
    c=row.get('components') or {}
    return {
      'expected_roi_pct':None,
      'expected_hold_hours':None,
      'worst_historical_drawdown_pct':abs(float(c['drawdown'])) if c.get('drawdown') is not None else None,
      'capital_efficiency_score':c.get('capital_efficiency'),
      'note':'ROI and hold-time expectations are not published unless supported by a comparable validated dataset.'}

def explanation(action:dict[str,Any],overall:float,risk:str)->str:
    verb={'KEEP_RUNNING':'Keep running','DEPLOY_TODAY':'Deploy today','WAIT':'Wait'}.get(action.get('action'),str(action.get('action')))
    reason=(action.get('supporting_reasons') or action.get('blocking_reasons') or ['Current evidence has been reconciled.'])[0]
    return f"{verb} {action.get('bot_name')}. Confidence {overall:.1f}%; risk {risk.lower()}. {reason}"

def update_history(payload:dict[str,Any])->None:
    old=load(HISTORY); records=old.get('records') if isinstance(old.get('records'),list) else []
    existing={r.get('recommendation_id') for r in records if isinstance(r,dict)}
    for rec in payload.get('recommendations') or []:
        if rec.get('recommendation_id') not in existing:
            records.append({'recorded_at':payload['generated_at'],'snapshot_id':payload['snapshot_id'],**rec,'outcome':{'status':'PENDING','closed_at':None,'realised_profit_pct':None,'notes':None}})
    history={'schema_version':'1.0','application_version':payload['application_version'],'generated_at':payload['generated_at'],'mode':'immutable_recommendation_audit_history','records':records[-500:]}
    HISTORY.write_text(json.dumps(history,indent=2),encoding='utf-8')

def build()->dict[str,Any]:
    dep=load(DOCS/'deployment_intelligence.json'); decisions=load(DOCS/'decision_intelligence_v28.json')
    generated=datetime.now(timezone.utc).isoformat(); recs=[]
    for a in dep.get('actions') or []:
        asset=str(a.get('asset') or '')
        ev=a.get('evidence') or {}
        rs,rst,rse=regime_score(a); hs,hst,hse,row=historical_score(asset,decisions); ls,lst,lse=live_score(a); cs,cst,cse=capital_score(a,str(dep.get('capital_status'))); ss,sst,sse=settings_score(a); aes,aest,aese=agreement_score(ev)
        components=(
          ConfidenceComponent('regime',rs,.25,rst,rse),ConfidenceComponent('historical',hs,.20,hst,hse),
          ConfidenceComponent('live_conditions',ls,.15,lst,lse),ConfidenceComponent('capital',cs,.15,cst,cse),
          ConfidenceComponent('settings',ss,.15,sst,sse),ConfidenceComponent('cross_source_agreement',aes,.10,aest,aese))
        overall=weighted(list(components)); risk=risk_level(a,overall,ev)
        seed={'asset':asset,'bot':a.get('bot_name'),'action':a.get('action'),'source':dep.get('snapshot_id'),'settings':a.get('recommended_settings'),'evidence':ev}
        rid=hashlib.sha256(json.dumps(seed,sort_keys=True).encode()).hexdigest()[:24]
        breakdown={str(k):round(float(v),3) for k,v in (row.get('components') or {}).items() if isinstance(v,(int,float))}
        prodcmp={'settings_changed':a.get('settings_changed'),'settings_state':a.get('settings_state'),'differences':a.get('settings_differences') or [],'recommended_settings':a.get('recommended_settings')}
        cap={'required':a.get('capital_required'),'available':a.get('capital_available'),'can_fund':a.get('can_fund'),'capital_status':dep.get('capital_status')}
        recs.append(RecommendationRecord(rid,asset,str(a.get('bot_name')),str(a.get('action')),overall,risk,components,breakdown,tuple(a.get('supporting_reasons') or ()),tuple(a.get('cautions') or ()),tuple(a.get('blocking_reasons') or ()),expected(row),prodcmp,cap,ev,explanation(a,overall,risk)))
    source={'deployment_snapshot':dep.get('snapshot_id'),'deployment_generated_at':dep.get('generated_at'),'decision_generated_at':decisions.get('generated_at')}
    snapshot=hashlib.sha256(json.dumps({'source':source,'ids':[r.recommendation_id for r in recs]},sort_keys=True).encode()).hexdigest()[:20]
    warnings=list(dep.get('warnings') or [])
    if any(r.expected_behaviour.get('expected_roi_pct') is None for r in recs):warnings.append('Expected ROI and hold time remain unpublished where comparable validated evidence is unavailable.')
    payload=RecommendationIntelligence('1.0',application_version(),generated,snapshot,'read_only_confidence_weighted_recommendation_intelligence',True,True,str(dep.get('overall_action') or 'WAIT'),str(dep.get('current_market_regime') or 'Unknown'),tuple(recs),'recommendation_history.json',tuple(dict.fromkeys(warnings)),source).to_dict()
    return payload

def main()->int:
    payload=build(); OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); update_history(payload); print(f'Recommendation intelligence written: {OUTPUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
