#!/usr/bin/env python3
"""V43 evidence-based gate for adding a second production asset.

The engine does not decide to trade. It answers whether CRM has enough evidence
for a human to review an additional coin and identifies the strongest candidate.
"""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'expansion_readiness.json'

def load(n):
    try:
        x=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return x if isinstance(x,dict) else {}
    except:return {}

def n(v):
    try:return float(v) if v not in (None,'') else None
    except:return None

def gate(label,state,detail,blocking=True): return {'label':label,'state':state,'detail':detail,'blocking':blocking}

def build():
    cap=load('capital_intelligence.json'); market=load('market_intelligence.json'); pipe=load('research_pipeline.json'); trades=load('trade_intelligence.json'); agent=load('local_agent_status.json'); three=load('threecommas.json')
    deploy=n(cap.get('deployable_capital')); breadth=n(market.get('breadth_score') or market.get('market_breadth_score') or market.get('breadth'))
    candidates=[x for x in pipe.get('candidates') or [] if isinstance(x,dict) and x.get('stage')=='READY_FOR_MANUAL_REVIEW']
    # Rank by current score, then independent Q1 closed-deal count.
    candidates=sorted(candidates,key=lambda x:(n(x.get('current_research_score')) or -1,n((x.get('q1_2026_metrics') or {}).get('closed_deals')) or -1),reverse=True)
    best=candidates[0] if candidates else None
    settings=(best or {}).get('frozen_settings') or {}
    # Existing walk-forward registry standard max capital is used only as an upper-bound evidence figure, never a required allocation.
    max_cap=n(((best or {}).get('q1_2026_metrics') or {}).get('max_capital')) or n(((best or {}).get('training_metrics') or {}).get('max_capital'))
    active=trades.get('trades') or []
    tel=[x for x in active if str(x.get('asset')).upper()=='TEL']
    tel_stress=any((x.get('monitoring_state') in {'LADDER_FULLY_USED','DURATION_REVIEW'}) for x in tel)
    gates=[]
    gates.append(gate('Local capital current','PASS' if str(agent.get('status')).upper()=='HEALTHY' else 'WAIT',f"Local agent: {agent.get('status') or 'Unknown'}"))
    gates.append(gate('3Commas trade state current','PASS' if str(three.get('status')).lower() in {'ok','partial'} else 'WAIT',f"3Commas: {three.get('status') or 'Unknown'}"))
    gates.append(gate('TEL active deal not in stress state','PASS' if not tel_stress else 'WAIT','No active TEL trade has exhausted its ladder or exceeded validated duration context.' if not tel_stress else 'Current TEL trade needs review before expanding.'))
    gates.append(gate('Independent candidate evidence','PASS' if best else 'WAIT',f"{best.get('asset')} has frozen Kraken/Q1 evidence." if best else 'No current candidate has passed both historical and independent validation.'))
    gates.append(gate('Market breadth supportive','PASS' if breadth is not None and breadth>=55 else 'WAIT',f"Breadth {breadth:.1f}%" if breadth is not None else 'Breadth unavailable.'))
    # Capital is a review gate because max_cap is a historical upper bound, not the intended live allocation.
    if deploy is None:
        cstate='WAIT'; cdetail='Deployable capital is unavailable.'
    elif deploy<=0:
        cstate='WAIT'; cdetail=f'Deployable capital is {deploy:.2f} USDT.'
    else:
        cstate='PASS'; cdetail=f'Deployable capital is {deploy:.2f} USDT; live allocation must be sized separately from historical max-capital evidence.'
    gates.append(gate('Capital headroom',cstate,cdetail))
    blocking=[x for x in gates if x['blocking'] and x['state']!='PASS']
    state='READY_FOR_MANUAL_REVIEW' if not blocking and best else 'WAIT'
    score=round(100*sum(1 for x in gates if x['state']=='PASS')/len(gates),1)
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'state':state,'score_pct':score,'recommended_next_candidate':best.get('asset') if best else None,'candidate':best,
      'deployable_capital':deploy,'historical_candidate_max_capital':max_cap,'gates':gates,
      'policy':{'one_new_asset_at_a_time':True,'manual_approval_required':True,'automatic_deployment':False,
        'principle':'Add a new asset only when capital, current TEL trade state, current market conditions and independent Kraken/Q1 evidence all support manual review.'},
      'next_action':('Review '+best.get('asset')+' for a small manual pilot allocation; do not copy historical max-capital mechanically.' if state=='READY_FOR_MANUAL_REVIEW' and best else 'Keep TEL as the only production asset until all expansion gates pass.')}
    payload['snapshot_id']=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:24]
    return payload

def main(): OUT.write_text(json.dumps(build(),indent=2),encoding='utf-8'); print(f'Expansion readiness written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
