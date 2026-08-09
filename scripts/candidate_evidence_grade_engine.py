#!/usr/bin/env python3
"""V52 candidate evidence-grade engine.

Grades deployment evidence by actual KuCoin history depth, bar count, time-span,
regime coverage, unseen validation and optional cross-exchange robustness.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'candidate_evidence_grades.json';POL=ROOT/'config'/'v52_execution_assurance_policy.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def loadp():
 try:return json.loads(POL.read_text(encoding='utf-8-sig'))
 except:return {}
def parse(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
 except:return None
def main():
 hist=load('historical_data_status.json');wf=load('kucoin_walk_forward.json');kr=load('walk_forward_registry.json');gm=load('global_market.json');p=loadp()
 grades=p.get('evidence_grades') or {};hby={str(x.get('symbol') or '').split('-')[0].upper():x for x in hist.get('inventory') or []}
 wby={str(x.get('asset') or '').upper():x for x in wf.get('assets') or []};kby={str(x.get('symbol') or '').replace('XBT','BTC').upper():x for x in kr.get('coins') or []};assets=sorted(set(hby)|set(wby)|set(kby));rows=[]
 for a in assets:
  h=hby.get(a) or {};w=wby.get(a) or {};k=kby.get(a) or {};bars=int(h.get('bars') or w.get('bars') or 0)
  start=parse(h.get('earliest') or h.get('start') or (w.get('period') or {}).get('start'));end=parse(h.get('latest') or h.get('end') or (w.get('period') or {}).get('end'))
  days=round((end-start).total_seconds()/86400,1) if start and end and end>=start else 0
  regimes=set()
  for name,prof in (w.get('regime_profiles') or {}).items():
   if prof and ((prof.get('training_metrics') or {}).get('closed_deals') is not None):regimes.add(str(name).upper())
  level='SCREEN_ONLY'
  if days>=float((grades.get('preliminary') or {}).get('minimum_days',180)) and bars>=int((grades.get('preliminary') or {}).get('minimum_bars',1000)):level='PRELIMINARY'
  if days>=float((grades.get('deployment_research') or {}).get('minimum_days',730)) and bars>=int((grades.get('deployment_research') or {}).get('minimum_bars',4000)):level='DEPLOYMENT_RESEARCH'
  if days>=float((grades.get('high_confidence') or {}).get('minimum_days',1095)) and bars>=int((grades.get('high_confidence') or {}).get('minimum_bars',6000)):level='HIGH_CONFIDENCE'
  ku_pass=bool(w.get('kucoin_primary_validation_pass'));krstatus=str(k.get('status') or 'MISSING').upper()
  deploy_history_ok=level in {'DEPLOYMENT_RESEARCH','HIGH_CONFIDENCE'}
  deployment_allowed=bool(deploy_history_ok and ku_pass)
  if level=='SCREEN_ONLY':reason='History is too short for deployment research; candidate may be screened/ranked only.'
  elif level=='PRELIMINARY':reason='Enough data for preliminary research, but not enough history/regime depth for normal deployment approval.'
  elif not ku_pass:reason='History depth is adequate, but unseen KuCoin walk-forward has not passed.'
  else:reason='History depth and unseen KuCoin walk-forward meet the normal deployment-evidence threshold.'
  rows.append({'asset':a,'pair':f'{a}-USDT','evidence_grade':level,'bars_4h':bars,'history_days':days,
    'history_start':start.isoformat() if start else None,'history_end':end.isoformat() if end else None,
    'history_years':round(days/365.25,2) if days else 0,'regime_profiles_observed':sorted(regimes),'regime_profile_count':len(regimes),
    'kucoin_walk_forward_pass':ku_pass,'kraken_robustness_status':krstatus,
    'kraken_role':'SECONDARY_ROBUSTNESS' if krstatus!='MISSING' else 'NOT_AVAILABLE',
    'deployment_history_gate':'PASS' if deploy_history_ok else 'BLOCKED','deployment_evidence_gate':'PASS' if deployment_allowed else 'BLOCKED',
    'reason':reason,'current_global_regime':gm.get('regime')})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'assets':rows,
  'summary':{'assets':len(rows),'screen_only':sum(x['evidence_grade']=='SCREEN_ONLY' for x in rows),'preliminary':sum(x['evidence_grade']=='PRELIMINARY' for x in rows),
  'deployment_research':sum(x['evidence_grade']=='DEPLOYMENT_RESEARCH' for x in rows),'high_confidence':sum(x['evidence_grade']=='HIGH_CONFIDENCE' for x in rows)},
  'principle':'Young assets are never treated as equally reliable to multi-year candidates. Kraken comparison is optional; unseen KuCoin validation is primary.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Evidence grades written: {OUT}; assets={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
