#!/usr/bin/env python3
"""V43 read-only active-deal intelligence.

Builds a snapshot of every currently active 3Commas deal, enriches it with
current recommendation and frozen Kraken/Q1 evidence, and reports what is known
without inventing probabilities. This engine never mutates a bot or order.
"""
from __future__ import annotations
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'trade_intelligence.json'

def load(name):
    try:
        x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
        return x if isinstance(x,dict) else {}
    except Exception:return {}

def num(v):
    try:return float(v) if v not in (None,'') else None
    except:return None

def age_hours(v):
    if not v:return None
    try:
        dt=datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
        return round((datetime.now(timezone.utc)-dt).total_seconds()/3600,2)
    except:return None

def pct_distance(current,target):
    c=num(current); t=num(target)
    if c in (None,0) or t is None:return None
    return round((t/c-1)*100,4)

def build():
    tc=load('threecommas.json'); rec=load('recommendation_intelligence.json'); wf=load('walk_forward_registry.json')
    reg={str(x.get('symbol') or '').upper():x for x in wf.get('coins') or [] if isinstance(x,dict)}
    recs={str(x.get('asset') or '').upper():x for x in rec.get('recommendations') or [] if isinstance(x,dict)}
    rows=[]
    for asset,bucket in (tc.get('assets') or {}).items():
        asset=str(asset).upper(); evidence=reg.get(asset) or {}; q1=evidence.get('q1_2026_metrics') or {}; recommendation=recs.get(asset) or {}
        for deal in bucket.get('deals') or []:
            if not isinstance(deal,dict):continue
            current=num(deal.get('current_price')); entry=num(deal.get('average_entry')); tp=num(deal.get('take_profit_price'))
            profit=num(deal.get('profit_pct')); completed=int(deal.get('completed_safety_orders') or 0); max_so=deal.get('max_safety_orders')
            try:max_so=int(max_so) if max_so is not None else None
            except:max_so=None
            remaining=max(0,max_so-completed) if max_so is not None else None
            hold=age_hours(deal.get('created_at'))
            q1avg=num(q1.get('average_hours')); q1long=num(q1.get('longest_hours'))
            duration_context='UNKNOWN'
            if hold is not None and q1avg is not None:
                duration_context='ABOVE_Q1_AVERAGE' if hold>q1avg else 'WITHIN_Q1_AVERAGE'
                if q1long is not None and hold>q1long: duration_context='BEYOND_Q1_LONGEST'
            monitoring='MONITOR'
            if remaining==0 and completed>0: monitoring='LADDER_FULLY_USED'
            if duration_context=='BEYOND_Q1_LONGEST': monitoring='DURATION_REVIEW'
            rows.append({
              'asset':asset,'bot_id':deal.get('bot_id'),'bot_name':deal.get('bot_name'),'pair':deal.get('pair'),
              'status':deal.get('status'),'opened_at':deal.get('created_at'),'hold_hours':hold,
              'profit_pct':profit,'profit_quote':deal.get('profit_usd'),'capital_used_quote':deal.get('capital_used_quote') or deal.get('capital_used'),
              'average_entry':entry,'current_price':current,'take_profit_price':tp,'distance_to_take_profit_pct':pct_distance(current,tp),
              'completed_safety_orders':completed,'max_safety_orders':max_so,'remaining_safety_orders':remaining,'active_safety_orders':deal.get('active_safety_orders'),
              'monitoring_state':monitoring,'crm_recommendation':recommendation.get('action'),'crm_confidence_pct':recommendation.get('overall_confidence'),
              'kraken_walk_forward_status':evidence.get('status'),'q1_average_hold_hours':q1avg,'q1_longest_hold_hours':q1long,'duration_context':duration_context,
              'evidence_note':'Historical context is descriptive only; CRM does not publish an exit probability without validated comparable outcome data.'
            })
    generated=tc.get('generated_at') or tc.get('last_success_at')
    age=None
    try:
        if generated:
            dt=datetime.fromisoformat(str(generated).replace('Z','+00:00')).astimezone(timezone.utc); age=round((datetime.now(timezone.utc)-dt).total_seconds()/60,1)
    except: pass
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'mode':'read_only_active_trade_intelligence','source':'3Commas active deal snapshots','snapshot_age_minutes':age,
      'monitoring_cadence':'snapshot-based; freshness follows the latest successful 3Commas refresh','real_time_streaming':False,
      'active_trade_count':len(rows),'trades':rows,'read_only':True,'manual_approval_required':True,
      'guardrails':{'bot_mutations':False,'order_mutations':False,'deal_closure':False,'probability_claims_without_evidence':False}}
    payload['snapshot_id']=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:24]
    return payload

def main():
    OUT.write_text(json.dumps(build(),indent=2),encoding='utf-8'); print(f'Trade intelligence written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
