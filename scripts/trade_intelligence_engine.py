#!/usr/bin/env python3
"""V43 read-only active-deal intelligence.

Builds a snapshot of every currently active 3Commas deal, enriches it with
current recommendation and frozen Kraken/Q1 evidence, and reports what is known
without inventing probabilities. This engine never mutates a bot or order.
"""
from __future__ import annotations
import hashlib,json,math,urllib.parse,urllib.request
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

def kucoin_symbol(pair,asset):
    p=str(pair or '').upper().replace('_','-')
    if p.endswith('-'+asset) or p.startswith('USDT-'): return f'{asset}-USDT'
    return p if '-' in p else f'{asset}-USDT'

def public_price(symbol):
    try:
        q=urllib.parse.urlencode({'symbol':symbol})
        req=urllib.request.Request('https://api.kucoin.com/api/v1/market/orderbook/level1?'+q,headers={'User-Agent':'Crypto-Regime-Manager/48.0','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=8) as r:
            p=json.loads(r.read().decode('utf-8'))
        return num(((p.get('data') or {}).get('price'))) if p.get('code')=='200000' else None
    except Exception:
        return None

def infer_entry(deal):
    entry=num(deal.get('average_entry'))
    if entry is not None:return entry,'3Commas'
    qty=num(deal.get('allocated_asset_quantity'));cost=num(deal.get('capital_used_quote') or deal.get('capital_used'))
    if qty and cost is not None and qty>0:return cost/qty,'capital_used / allocated_quantity'
    return None,'unavailable'

def bot_for(bucket,deal):
    bid=deal.get('bot_id')
    return next((b for b in bucket.get('bots') or [] if b.get('bot_id')==bid),{})

def infer_tp(entry,deal,bot):
    explicit=num(deal.get('take_profit_price'))
    if explicit is not None:return explicit,'3Commas deal'
    pct=num(bot.get('take_profit_pct'))
    if entry is not None and pct is not None:return entry*(1+pct/100),'average entry + live bot TP%'
    return None,'unavailable'

def build():
    tc=load('threecommas.json'); rec=load('recommendation_intelligence.json'); wf=load('walk_forward_registry.json'); recon=load('execution_reconciliation.json')
    reg={str(x.get('symbol') or '').upper():x for x in wf.get('coins') or [] if isinstance(x,dict)}
    recs={str(x.get('asset') or '').upper():x for x in rec.get('recommendations') or [] if isinstance(x,dict)}
    stale={(str(x.get('asset') or '').upper(),x.get('bot_id')) for x in recon.get('deals') or [] if isinstance(x,dict) and x.get('reconciliation_state')=='PROVIDER_STALE_OPEN'}
    rows=[]
    for asset,bucket in (tc.get('assets') or {}).items():
        asset=str(asset).upper(); evidence=reg.get(asset) or {}; q1=evidence.get('q1_2026_metrics') or {}; recommendation=recs.get(asset) or {}
        for deal in bucket.get('deals') or []:
            if (asset,deal.get('bot_id')) in stale: continue
            if not isinstance(deal,dict):continue
            bot=bot_for(bucket,deal)
            entry,entry_source=infer_entry(deal)
            symbol=kucoin_symbol(deal.get('pair'),asset)
            current=num(deal.get('current_price')) or public_price(symbol)
            tp,tp_source=infer_tp(entry,deal,bot)
            profit=num(deal.get('profit_pct'))
            profit_quote=num(deal.get('profit_usd'))
            if profit_quote is None and current is not None and entry is not None:
                qty=num(deal.get('allocated_asset_quantity'))
                if qty is not None: profit_quote=round((current-entry)*qty,8)
            completed=int(deal.get('completed_safety_orders') or 0); max_so=deal.get('max_safety_orders')
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
              'profit_pct':profit,'profit_quote':profit_quote,'capital_used_quote':deal.get('capital_used_quote') or deal.get('capital_used'),
              'average_entry':entry,'average_entry_source':entry_source,'current_price':current,'current_price_source':'KuCoin public level1' if current is not None and deal.get('current_price') is None else '3Commas','take_profit_price':tp,'take_profit_price_source':tp_source,'distance_to_take_profit_pct':pct_distance(current,tp),
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
