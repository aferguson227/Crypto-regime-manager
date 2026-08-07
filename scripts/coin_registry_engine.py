#!/usr/bin/env python3
"""V44 persistent coin lifecycle registry generated from all known CRM evidence."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'coin_registry.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
 except:return {}
def main():
 strategies=load('strategies.json'); pipe=load('research_pipeline.json'); rec=load('recommendation_intelligence.json'); recommended=load('recommended_bots.json'); globalm=load('global_market.json')
 assets={}
 def ensure(a):
  a=str(a or '').upper();
  if not a:return None
  return assets.setdefault(a,{'asset':a,'status':'WATCHLIST','reasons':[],'current_recommendation':None,'research_stage':None,'history_sources':[]})
 for r in ((strategies.get('portfolio') or {}).get('ranking') or []):
  if not isinstance(r,dict):continue
  x=ensure(r.get('id')); x['status']='LIVE' if str(r.get('classification'))=='forward_testing' else ('WATCHLIST' if r.get('entry_allowed') else 'ARCHIVED'); x['reasons'].append(f"Strategy classification: {r.get('classification')}; action: {r.get('action')}"); x['history_sources'].append('strategies')
 for r in ((strategies.get('portfolio') or {}).get('research') or []):
  if not isinstance(r,dict):continue
  x=ensure(r.get('id')); x['status']='ARCHIVED' if 'FAIL' in str(r.get('promotion_status')).upper() else 'RESEARCH'; x['reasons'].append(str(r.get('promotion_status') or 'Research asset')); x['history_sources'].append('strategies.research')
 for c in pipe.get('candidates') or []:
  if not isinstance(c,dict):continue
  x=ensure(c.get('asset')); x['research_stage']=c.get('stage'); x['history_sources'].append('research_pipeline')
  if c.get('stage')=='READY_FOR_MANUAL_REVIEW' and x['status'] not in {'LIVE'}:x['status']='READY_FOR_REVIEW'
  if c.get('stage')=='RESEARCH_REJECT':x['status']='REJECTED'
  x['reasons'].append(c.get('next_action') or '')
 for r in rec.get('recommendations') or []:
  if not isinstance(r,dict):continue
  x=ensure(r.get('asset')); x['current_recommendation']=r.get('action'); x['recommendation_confidence_pct']=r.get('overall_confidence'); x['history_sources'].append('recommendation_intelligence')
  if r.get('action')=='DEPLOY_TODAY':x['status']='DEPLOYMENT_CANDIDATE'
 for c in recommended.get('candidates') or []:
  if not isinstance(c,dict):continue
  x=ensure(c.get('asset')); x['validated_return_pct']=((c.get('profitability_evidence') or {}).get('q1_return_on_max_capital_pct')); x['history_sources'].append('recommended_bots')
 for x in assets.values():
  x['reasons']=[r for r in dict.fromkeys(x['reasons']) if r][:5]; x['history_sources']=sorted(set(x['history_sources'])); x['global_regime']=globalm.get('regime')
 rows=sorted(assets.values(),key=lambda x:({'LIVE':0,'DEPLOYMENT_CANDIDATE':1,'READY_FOR_REVIEW':2,'WATCHLIST':3,'RESEARCH':4,'ARCHIVED':5,'REJECTED':6}.get(x['status'],9),x['asset']))
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'coin_count':len(rows),'coins':rows,'policy':{'never_forget_analysed_coin':True,'automatic_live_deployment':False}}
 payload['snapshot_id']=hashlib.sha256(json.dumps([(x['asset'],x['status'],x.get('current_recommendation')) for x in rows],sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Coin registry written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
