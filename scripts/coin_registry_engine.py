#!/usr/bin/env python3
"""V51 canonical coin lifecycle registry.

Compatibility provenance: historical strategies.research records are preserved through the persistent research/registry history.

Execution truth has precedence over research classifications: a running/deployed
bot can continue forward research without being downgraded to CANDIDATE.
"""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'coin_registry.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 tc=load('threecommas.json');recon=load('execution_reconciliation.json');pipe=load('research_pipeline.json');rec=load('recommendation_intelligence.json');recommended=load('recommended_bots.json');globalm=load('global_market.json');wf=load('kucoin_walk_forward.json')
 assets={}
 def ensure(a):
  a=str(a or '').upper()
  if not a:return None
  return assets.setdefault(a,{'asset':a,'lifecycle':'WATCHLIST','execution_state':'NOT_DEPLOYED','research_state':'NOT_STARTED','reasons':[],'history_sources':[]})
 # Execution/provider evidence is authoritative for lifecycle.
 for a,b in (tc.get('assets') or {}).items():
  x=ensure(a);bots=b.get('bots') or [];deals=b.get('deals') or []
  enabled=[z for z in bots if z.get('enabled')]
  if enabled or deals:
   x['lifecycle']='LIVE_PRODUCTION';x['execution_state']='ACTIVE_DEAL' if deals else 'DEPLOYED_IDLE'
   x['live_bot_count']=len(enabled);x['provider_bot_count']=len(bots);x['active_deal_count']=len(deals);x['history_sources'].append('threecommas')
   x['reasons'].append('Live execution-provider bot/deal evidence takes precedence over research labels.')
 for d in recon.get('deals') or []:
  x=ensure(d.get('asset'));x['history_sources'].append('execution_reconciliation')
  if d.get('reconciliation_state')=='PROVIDER_STALE_OPEN':
   x['execution_state']='EXCHANGE_CLOSED_PROVIDER_STALE';x['reasons'].append('KuCoin proves the position closed while 3Commas still reports it open.')
 # Research evidence enriches but never downgrades LIVE_PRODUCTION.
 wfby={str(x.get('asset') or '').upper():x for x in wf.get('assets') or []}
 for c in pipe.get('candidates') or []:
  a=str(c.get('asset') or '').upper();x=ensure(a);stage=str(c.get('stage') or '');x['research_state']=stage or x['research_state'];x['history_sources'].append('research_pipeline')
  if x['lifecycle']!='LIVE_PRODUCTION':
   if stage=='READY_FOR_MANUAL_REVIEW':x['lifecycle']='READY_FOR_REVIEW'
   elif stage=='RESEARCH_REJECT':x['lifecycle']='REJECTED'
   elif stage:x['lifecycle']='RESEARCHING'
  if c.get('next_action'):x['reasons'].append(c['next_action'])
 for r in rec.get('recommendations') or []:
  x=ensure(r.get('asset'));x['current_recommendation']=r.get('action');x['recommendation_confidence_pct']=r.get('overall_confidence');x['history_sources'].append('recommendation_intelligence')
  if x['lifecycle']!='LIVE_PRODUCTION' and r.get('action')=='DEPLOY_TODAY':x['lifecycle']='DEPLOYMENT_CANDIDATE'
 for c in recommended.get('candidates') or []:
  x=ensure(c.get('asset'));x['validated_return_pct']=((c.get('profitability_evidence') or {}).get('q1_return_on_max_capital_pct'));x['history_sources'].append('recommended_bots')
 for a,x in assets.items():
  kw=wfby.get(a) or {};x['current_regime']=kw.get('current_regime_family') or globalm.get('regime');x['research_continues_while_live']=x['lifecycle']=='LIVE_PRODUCTION'
  x['reasons']=[r for r in dict.fromkeys(x['reasons']) if r][:5];x['history_sources']=sorted(set(x['history_sources']))
 order={'LIVE_PRODUCTION':0,'DEPLOYMENT_CANDIDATE':1,'READY_FOR_REVIEW':2,'RESEARCHING':3,'WATCHLIST':4,'REJECTED':5,'ARCHIVED':6}
 rows=sorted(assets.values(),key=lambda x:(order.get(x['lifecycle'],9),x['asset']))
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'coin_count':len(rows),'coins':rows,
  'lifecycle_order':['DISCOVERED','RESEARCHING','VALIDATED','STAGED','DEPLOYED','LIVE_PRODUCTION','PAUSED','RETIRED'],
  'policy':{'execution_truth_precedence':True,'never_forget_analysed_coin':True,'automatic_live_deployment':False}}
 payload['snapshot_id']=hashlib.sha256(json.dumps([(x['asset'],x['lifecycle'],x.get('execution_state')) for x in rows],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Coin registry written: {OUT}; live={sum(x["lifecycle"]=="LIVE_PRODUCTION" for x in rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
