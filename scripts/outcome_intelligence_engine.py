#!/usr/bin/env python3
"""V32.6 read-only recommendation outcome reconciliation and analytics.

Historical recommendation records are never rewritten. Optional manual outcome
annotations are read from data/outcomes/manual_outcomes.json. Live 3Commas data
is used only to reconcile observable active deals; it never changes trading state.
"""
from __future__ import annotations
import json, math, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.outcome_intelligence import OutcomeIntelligence, OutcomeRecord
DOCS=ROOT/'docs'; OUTPUT=DOCS/'outcome_intelligence.json'; MANUAL=ROOT/'data'/'outcomes'/'manual_outcomes.json'
VALID_STATUSES={'PENDING','ACTIVE','COMPLETED','IGNORED','EXPIRED','CANCELLED','SUPERSEDED'}

def load(path:Path)->Any:
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception:return {}

def num(v:Any)->float|None:
    try:
        f=float(v)
        return f if math.isfinite(f) else None
    except (TypeError,ValueError):return None

def iso_hours(start:Any,end:Any)->float|None:
    if not start or not end:return None
    try:
        a=datetime.fromisoformat(str(start).replace('Z','+00:00')); b=datetime.fromisoformat(str(end).replace('Z','+00:00'))
        return round(max(0,(b-a).total_seconds()/3600),2)
    except Exception:return None

def manual_map()->dict[str,dict[str,Any]]:
    raw=load(MANUAL); rows=raw.get('outcomes',[]) if isinstance(raw,dict) else []
    return {str(r.get('recommendation_id')):r for r in rows if isinstance(r,dict) and r.get('recommendation_id')}

def active_deals()->list[dict[str,Any]]:
    raw=load(DOCS/'threecommas.json'); out=[]
    for asset,block in (raw.get('assets') or {}).items():
        for deal in block.get('deals') or []:
            if isinstance(deal,dict):out.append({'asset':asset,**deal})
    return out

def match_deal(rec:dict[str,Any],deals:list[dict[str,Any]])->dict[str,Any]|None:
    asset=str(rec.get('asset') or '').upper(); bot=str(rec.get('bot_name') or '').lower()
    candidates=[d for d in deals if str(d.get('asset') or '').upper()==asset]
    exact=next((d for d in candidates if str(d.get('bot_name') or '').lower()==bot),None)
    return exact or (candidates[0] if len(candidates)==1 else None)

def calculate_correct(action:str,status:str,profit_pct:float|None,manual:dict[str,Any])->bool|None:
    if isinstance(manual.get('correct'),bool):return manual['correct']
    if status!='COMPLETED' or profit_pct is None:return None
    if action in {'DEPLOY_TODAY','KEEP_RUNNING'}:return profit_pct>0
    if action=='WAIT':return profit_pct<=0
    return None

def record_from(rec:dict[str,Any],deal:dict[str,Any]|None,manual:dict[str,Any],regime:str|None)->OutcomeRecord:
    action=str(rec.get('action') or 'WAIT').upper(); status=str(manual.get('status') or '').upper()
    if status not in VALID_STATUSES:status='ACTIVE' if deal and action in {'KEEP_RUNNING','DEPLOY_TODAY'} else 'PENDING'
    source='manual' if manual else ('threecommas_read_only' if deal else 'recommendation_history')
    acted=manual.get('acted_on_at') or (deal or {}).get('created_at')
    closed=manual.get('closed_at')
    entry=num(manual.get('entry_price')); exitp=num(manual.get('exit_price'))
    profit=num(manual.get('realised_profit_pct'))
    if profit is None and status=='ACTIVE':profit=num((deal or {}).get('profit_pct'))
    profit_value=num(manual.get('realised_profit_value'))
    hold=num(manual.get('hold_hours'))
    if hold is None:hold=iso_hours(acted,closed)
    evidence={'threecommas_deal_observed':bool(deal),'deal_status':(deal or {}).get('status'),'completed_safety_orders':(deal or {}).get('completed_safety_orders'),'manual_annotation_present':bool(manual)}
    return OutcomeRecord(
      str(rec.get('recommendation_id')),rec.get('snapshot_id'),rec.get('recorded_at'),str(rec.get('asset') or ''),str(rec.get('bot_name') or ''),action,
      num(rec.get('overall_confidence')),regime,status,source,acted,closed,entry,exitp,profit_value,profit,
      num(manual.get('maximum_adverse_excursion_pct')),num(manual.get('maximum_favourable_excursion_pct')),hold,
      calculate_correct(action,status,profit,manual),manual.get('notes'),evidence)

def group_metrics(records:list[OutcomeRecord],key)->dict[str,Any]:
    groups:dict[str,list[OutcomeRecord]]={}
    for r in records:groups.setdefault(str(key(r) or 'Unknown'),[]).append(r)
    out={}
    for name,rows in sorted(groups.items()):
        completed=[r for r in rows if r.status=='COMPLETED']; judged=[r for r in completed if r.correct is not None]; returns=[r.realised_profit_pct for r in completed if r.realised_profit_pct is not None]
        out[name]={'recommendations':len(rows),'completed':len(completed),'judged':len(judged),'correct':sum(r.correct is True for r in judged),'accuracy_pct':round(100*sum(r.correct is True for r in judged)/len(judged),1) if judged else None,'average_return_pct':round(sum(returns)/len(returns),3) if returns else None}
    return out

def calibration(records:list[OutcomeRecord])->tuple[dict[str,Any],...]:
    bands=[(0,50),(50,65),(65,80),(80,90),(90,101)]; out=[]
    for lo,hi in bands:
        rows=[r for r in records if r.recommendation_confidence is not None and lo<=r.recommendation_confidence<hi]
        judged=[r for r in rows if r.status=='COMPLETED' and r.correct is not None]
        observed=round(100*sum(r.correct is True for r in judged)/len(judged),1) if judged else None
        midpoint=round((lo+min(hi,100))/2,1)
        out.append({'band':f'{lo}-{min(hi,100)}%','recommendations':len(rows),'completed_and_judged':len(judged),'expected_confidence_midpoint_pct':midpoint,'observed_accuracy_pct':observed,'calibration_error_pct':round(observed-midpoint,1) if observed is not None else None})
    return tuple(out)

def build()->dict[str,Any]:
    hist=load(DOCS/'recommendation_history.json'); manual=manual_map(); deals=active_deals(); regime=(load(DOCS/'recommendation_intelligence.json') or {}).get('market_regime')
    rows=[r for r in hist.get('records',[]) if isinstance(r,dict)] if isinstance(hist,dict) else []
    records=[record_from(r,match_deal(r,deals),manual.get(str(r.get('recommendation_id')),{ }),regime) for r in rows]
    completed=[r for r in records if r.status=='COMPLETED']; judged=[r for r in completed if r.correct is not None]; returns=[r.realised_profit_pct for r in completed if r.realised_profit_pct is not None]
    analytics={'total_recommendations':len(records),'pending':sum(r.status=='PENDING' for r in records),'active':sum(r.status=='ACTIVE' for r in records),'completed':len(completed),'ignored':sum(r.status=='IGNORED' for r in records),'expired':sum(r.status=='EXPIRED' for r in records),'superseded':sum(r.status=='SUPERSEDED' for r in records),'judged_outcomes':len(judged),'correct_outcomes':sum(r.correct is True for r in judged),'overall_accuracy_pct':round(100*sum(r.correct is True for r in judged)/len(judged),1) if judged else None,'average_realised_return_pct':round(sum(returns)/len(returns),3) if returns else None,'by_asset':group_metrics(records,lambda r:r.asset),'by_action':group_metrics(records,lambda r:r.recommended_action),'by_regime':group_metrics(records,lambda r:r.market_regime)}
    warnings=[]
    if not MANUAL.exists():warnings.append('No manual outcome file is present. Completed outcome metrics remain unavailable until outcomes are recorded or reconciled from closed deals.')
    if not completed:warnings.append('No completed recommendation outcomes are available yet; accuracy and calibration are intentionally unknown.')
    payload=OutcomeIntelligence('1.0',application_version(),datetime.now(timezone.utc).isoformat(),'read_only_outcome_reconciliation',True,True,tuple(records),analytics,calibration(records),{'recommendation_history':'recommendation_history.json','manual_outcomes':str(MANUAL.relative_to(ROOT)) if MANUAL.exists() else None,'threecommas':'threecommas.json'},tuple(warnings)).to_dict()
    return payload

def main()->int:
    payload=build(); OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Outcome intelligence written: {OUTPUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
