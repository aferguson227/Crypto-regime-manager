#!/usr/bin/env python3
"""V58 governed deployment lifecycle and canonical bot setup packages.

Creates one provider-independent specification for:
RESEARCHING → VALIDATING → READY_TO_DEPLOY → RECOMMENDED_NOW → ACTIVE

No live bot/order mutation is implemented.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'deployment_lifecycle.json'

# Historical V58 regression marker only: pct==100 remains superseded by optimisation_complete + continuation_resolved + capital_ready.
REQUIRED=['base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders',
          'volume_scale','step_scale','max_active_safety_orders','max_active_deals','start_condition','order_type',
          'trailing_enabled','cooldown_seconds']

def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def asset(v):return str(v or '').upper().replace('/USDT','').replace('-USDT','').replace('USDT_','').replace('_USDT','')
def norm_settings(s):
 s=dict(s or {})
 aliases={'max_safety_orders':'safety_orders','safety_order_deviation_pct':'so_deviation_pct',
          'start_order_type':'order_type','cooldown':'cooldown_seconds'}
 for old,new in aliases.items():
  if s.get(new) is None and s.get(old) is not None:s[new]=s.get(old)
 return {k:s.get(k) for k in REQUIRED}
def completeness(s):
 missing=[k for k,v in s.items() if v is None]
 return round(100*(len(s)-len(missing))/len(s),1),missing
def main():
 review=load('candidate_review.json');profiles=load('live_bot_profiles.json');alloc=load('portfolio_allocation_recommendations.json');specs=load('dca_deployment_specs.json')
 workspace=load('professional_workspace.json');three=load('threecommas.json')
 alby={asset(x.get('asset')):x for x in alloc.get('recommendations') or []};spby={asset(x.get('asset')):x for x in specs.get('specs') or []}
 rows=[]

 # Active production bots first.
 for b in profiles.get('bots') or []:
  a=asset(b.get('asset') or b.get('pair'));live=norm_settings(b.get('live_settings') or {})
  pct,missing=completeness(live)
  active=bool(b.get('enabled') or b.get('active_deals') or str(b.get('action') or '').upper() in {'KEEP_ACTIVE_DEAL','KEEP_RUNNING'})
  if not active:continue
  rows.append({'asset':a,'pair':f'{a}-USDT','bot_name':b.get('bot_name') or b.get('name') or f'{a} bot',
   'lifecycle_state':'ACTIVE','priority':1,'recommended_action':b.get('action') or 'KEEP_ACTIVE',
   'settings':live,'settings_completeness_pct':pct,'missing_settings':missing,
   'allocation_usdt':b.get('reserve_capital') or b.get('allocated_capital'),
   'source':'LIVE_PRODUCTION_PROFILE','button_label':'View bot settings',
   'deployment_allowed':False,'automatic_deployment':False,
   'explanation':'This strategy is already active. Use the setup panel to inspect the live configuration and any recommended changes.'})

 # Research/deployment candidates.
 for c in review.get('candidates') or []:
  a=asset(c.get('asset'));sp=spby.get(a) or {}
  strategy=dict(sp.get('recommended_dca_settings') or {});controls=dict(sp.get('governed_execution_controls') or {})
  optimisation_complete=bool(sp.get('recommended_settings_available')) and str(sp.get('optimisation_status') or '').upper()=='COMPLETE'
  pct=float(sp.get('optimisation_progress_pct') or (100 if optimisation_complete else 0))
  missing=[] if optimisation_complete else ['DCA optimisation is still in progress; exact Recommended DCA Settings are deliberately withheld.']
  gates=c.get('gates') or [];mandatory_pass=bool(gates) and all(g.get('state')=='PASS' for g in gates)
  kr=(c.get('kraken_robustness') or {});kr_status=str(kr.get('status') or 'MISSING').upper()
  cont=(kr.get('continuation') or {})
  continuation_state=str(cont.get('continuation_status') or '').upper()
  continuation_resolved=kr_status!='FAIL' or bool(cont.get('terminal')) or continuation_state in {'CLOSED_ON_KUCOIN_CONTINUATION','STILL_OPEN','RESOLVED','PASS'}
  al=alby.get(a) or {};allocation=al.get('recommended_allocation_usdt') if al.get('recommended_allocation_usdt') is not None else c.get('suggested_allocation_usdt')
  required=sp.get('capital_required_usdt')
  capital_ready=bool(allocation is not None and float(allocation or 0)>0 and (required is None or float(allocation)>=float(required)))
  ready_review=bool(c.get('readiness_pct')==100 or c.get('deployment_preparation_available') or optimisation_complete)
  ready_to_deploy=bool(mandatory_pass and optimisation_complete and continuation_resolved and capital_ready)
  if ready_to_deploy:state='READY_TO_DEPLOY'
  elif not optimisation_complete and c.get('kucoin_profitability'):state='DCA_OPTIMISATION_IN_PROGRESS'
  elif ready_review:state='READY_FOR_DEPLOYMENT_REVIEW'
  elif c.get('adaptive_research'):state='VALIDATING'
  else:state='RESEARCHING'
  blockers=[]
  if not mandatory_pass:
   pending=[str(g.get('label') or g.get('id') or 'Evidence gate') for g in gates if g.get('state')!='PASS']
   if pending:blockers.append('Evidence still required: '+', '.join(pending)+'.')
  if not optimisation_complete:blockers.append('DCA settings optimisation is in progress. CRM will not publish exact recommended settings until unseen KuCoin validation passes.')
  if not continuation_resolved:
   detail=str(cont.get('reason') or '')
   blockers.append('Independent continuation evidence has not reached a terminal result'+(f' · {detail}' if detail else f' · current status {continuation_state or "unknown"}')+'.')
  if allocation is None or float(allocation or 0)<=0:blockers.append('No portfolio capital is currently safe to allocate to a new bot.')
  elif required is not None and float(allocation)<float(required):blockers.append(f'Current safe allocation {float(allocation):.2f} USDT is below this setup\'s required capital {float(required):.2f} USDT.')
  rows.append({'asset':a,'pair':c.get('pair') or f'{a}-USDT','bot_name':f'{a} Regime DCA',
   'lifecycle_state':state,'priority':2 if state=='READY_TO_DEPLOY' else 3,
   'recommended_action':'DEPLOY' if state=='READY_TO_DEPLOY' else 'CONTINUE_OPTIMISATION' if state=='DCA_OPTIMISATION_IN_PROGRESS' else 'REVIEW' if ready_review else 'CONTINUE_RESEARCH',
   'settings':strategy if optimisation_complete else {},'governed_execution_controls':controls if optimisation_complete else {},'settings_completeness_pct':pct,'missing_settings':missing,'dca_optimisation_status':sp.get('optimisation_status'),
   'entry_trigger':c.get('entry_trigger'),'current_regime':c.get('current_regime'),
   'allocation_usdt':allocation,'capital_required_usdt':required,'capital_sizing_status':sp.get('capital_sizing_status'),'setting_sources':sp.get('setting_sources') or {},'readiness_pct':c.get('readiness_pct'),
   'kraken_robustness':kr,'kucoin_profitability':c.get('kucoin_profitability') or {},
   'blockers':blockers,'source':'GOVERNED_CANDIDATE_REVIEW',
   'button_label':'View deployment plan' if state!='READY_TO_DEPLOY' else 'View setup & deploy manually',
   'deployment_allowed':state=='READY_TO_DEPLOY','automatic_deployment':False,
   'explanation':('All mandatory evidence, exact settings and capital-allocation gates have passed. Manual deployment is permitted.' if state=='READY_TO_DEPLOY'
                  else ('Strategy validation is complete; live deployment is waiting only for safe portfolio capital.' if mandatory_pass and optimisation_complete and continuation_resolved and not capital_ready
                        else 'Review the specific remaining requirement(s). CRM promotes this candidate automatically when every mandatory gate passes.'))})

 # Rank READY_TO_DEPLOY candidates; only the preferred eligible use of capital becomes RECOMMENDED_NOW.
 eligible=[x for x in rows if x['lifecycle_state']=='READY_TO_DEPLOY']
 if eligible:
  eligible.sort(key=lambda x:(-(float(x.get('readiness_pct') or 0)),
                              -(float((x.get('kucoin_profitability') or {}).get('validation_return_on_max_capital_pct') or -999))))
  preferred=eligible[0]
  preferred['lifecycle_state']='RECOMMENDED_NOW';preferred['priority']=0;preferred['recommended_action']='DEPLOY'
  preferred['explanation']='Of the candidates currently Ready to Deploy, CRM ranks this as the preferred next use of available capital.'

 rows.sort(key=lambda x:(x.get('priority',9),x.get('asset','')))
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
  'workflow':['RESEARCHING','VALIDATING','DCA_OPTIMISATION_IN_PROGRESS','READY_FOR_DEPLOYMENT_REVIEW','READY_TO_DEPLOY','RECOMMENDED_NOW','ACTIVE'],
  'bots':rows,
  'summary':{'active':sum(x['lifecycle_state']=='ACTIVE' for x in rows),
             'ready_for_review':sum(x['lifecycle_state']=='READY_FOR_DEPLOYMENT_REVIEW' for x in rows),
             'ready_to_deploy':sum(x['lifecycle_state']=='READY_TO_DEPLOY' for x in rows),
             'recommended_now':sum(x['lifecycle_state']=='RECOMMENDED_NOW' for x in rows)},
  'provider_independent':True,'automatic_live_deployment':False,
  'principle':'Fixing Kraken continuation removes a blocker; it does not itself create a trading signal. Promotion occurs only after all gates pass and the candidate wins governed portfolio ranking.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"Deployment lifecycle: active={payload['summary']['active']} ready={payload['summary']['ready_to_deploy']} recommended={payload['summary']['recommended_now']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
