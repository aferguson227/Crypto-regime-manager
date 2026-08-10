#!/usr/bin/env python3
"""V49 autonomous candidate discovery and cached background research scheduler."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts import research_database as db

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'research_scheduler_status.json'
POLICY=ROOT/'config'/'v49_autonomy_policy.json';KPOL=ROOT/'config'/'kucoin_research_policy.json';RPOL=ROOT/'config'/'research_policy.json'

def now():return datetime.now(timezone.utc).isoformat()
def load(p,default=None):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def run(mod,*args,check=True):
 r=subprocess.run([sys.executable,'-m',mod,*args],cwd=ROOT,text=True,capture_output=True)
 if r.stdout:print(r.stdout,end='')
 if r.stderr:print(r.stderr,end='',file=sys.stderr)
 if check and r.returncode:raise RuntimeError(f'{mod} failed ({r.returncode})')
 return r
def age_minutes(ts):
 try:return (datetime.now(timezone.utc)-datetime.fromisoformat(str(ts).replace('Z','+00:00'))).total_seconds()/60
 except:return 1e12
def file_sig(path):
 p=Path(path)
 if not p.exists():return 'missing'
 st=p.stat();return f'{p.name}:{st.st_size}:{int(st.st_mtime)}'
def history_root():
 raw=os.getenv('CRM_DATA_ROOT');base=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 return base/'KuCoin'/'4h'
def research_fingerprint():
 parts=[file_sig(POLICY),file_sig(KPOL),file_sig(RPOL),file_sig(DOCS/'adaptive_research_queue.json')]
 h=history_root()
 if h.exists():
  for p in sorted(h.glob('*_4H.csv')):parts.append(file_sig(p))
 disc=load(DOCS/'coin_discovery.json')
 parts.append(json.dumps([(x.get('symbol'),x.get('rank'),x.get('research_score')) for x in (disc.get('researched_candidates') or [])],sort_keys=True))
 return hashlib.sha256('|'.join(parts).encode()).hexdigest()
def due(key,minutes):
 return age_minutes(db.get_meta(key))>=minutes
def write(payload):
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');return payload
def status_only():
 db.migrate();db.record_assets();db.import_candidate_state();p=load(POLICY);hist=load(DOCS/'historical_data_status.json');wf=load(DOCS/'kucoin_walk_forward.json');disc=load(DOCS/'coin_discovery.json')
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'mode':'status_only',
  'market_scan':{'known_eligible':len(disc.get('shortlist') or []),'last_run':db.get_meta('last_market_scan'),'next_due_minutes':max(0,round(float(p.get('market_scan_minutes',60))-age_minutes(db.get_meta('last_market_scan')),1))},
  'history':{'ready':hist.get('research_ready_count',0),'total':hist.get('candidate_count',0),'progress_pct':hist.get('progress_pct',0),'last_run':db.get_meta('last_history_sync')},
  'research':{'last_run':db.get_meta('last_research_cycle'),'last_fingerprint':db.get_meta('last_research_fingerprint'),'ready_for_review':(wf.get('summary') or {}).get('ready_for_manual_review',0)},
  'database':db.write_status(),'status':'READY','installer_runs_expensive_backtests':False}
 return write(payload)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--status-only',action='store_true');ap.add_argument('--force',action='store_true');args=ap.parse_args()
 if args.status_only:return 0 if status_only() else 0
 db.migrate();p=load(POLICY);started=time.monotonic();activity=[];backtests=0
 run('scripts.kraken_validation_evidence_manager',check=False);run('scripts.cross_exchange_continuation_engine',check=False);run('scripts.continuation_acquisition_queue_engine',check=False)
 run('scripts.adaptive_candidate_research_engine',check=False)
 # Full KuCoin USDT scan hourly. Failure does not destroy existing research.
 if args.force or due('last_market_scan',float(p.get('market_scan_minutes',60))):
  st=time.monotonic()
  r=run('scripts.coin_discovery',check=False)
  activity.append({'stage':'Market scan','status':'COMPLETE' if r.returncode==0 else 'DEGRADED','seconds':round(time.monotonic()-st,2)})
  if r.returncode==0:db.set_meta('last_market_scan',now());db.record_assets()
 # History grows every cycle, but bounded by historical_data_manager policy.
 st=time.monotonic();r=run('scripts.historical_data_manager','--sync',check=False)
 activity.append({'stage':'KuCoin history','status':'COMPLETE' if r.returncode==0 else 'DEGRADED','seconds':round(time.monotonic()-st,2)})
 if r.returncode==0:db.set_meta('last_history_sync',now())
 # Same-cycle continuation re-evaluation after fresh KuCoin history lands.
 run('scripts.cross_exchange_continuation_engine',check=False);run('scripts.continuation_acquisition_queue_engine',check=False)
 fp=research_fingerprint();old=db.get_meta('last_research_fingerprint')
 force_age=age_minutes(db.get_meta('last_research_cycle'))>=float(p.get('full_revalidation_hours',24))*60
 research_due=args.force or fp!=old or force_age
 if research_due:
  st=time.monotonic();r1=run('scripts.regime_backtest_engine',check=False);r2=run('scripts.kucoin_walk_forward_engine',check=False)
  duration=round(time.monotonic()-st,2)
  reg=load(DOCS/'regime_backtest_intelligence.json');wf=load(DOCS/'kucoin_walk_forward.json')
  backtests=int((reg.get('summary') or {}).get('backtests_run') or 0)+int((wf.get('summary') or {}).get('backtests_run') or 0)
  ok=r1.returncode==0 and r2.returncode==0
  activity.append({'stage':'Cached optimisation + walk-forward','status':'COMPLETE' if ok else 'DEGRADED','seconds':duration,'backtests':backtests,'cache_reason':'fingerprint changed' if fp!=old else 'periodic revalidation'})
  if ok:
   db.set_meta('last_research_cycle',now());db.set_meta('last_research_fingerprint',fp)
   db.cache_put('latest_research_bundle',fp,{'regime':reg,'walk_forward':wf},duration)
   db.import_candidate_state();run('scripts.adaptive_candidate_research_engine',check=False)
 else:
  cached=db.cache_get('latest_research_bundle',fp)
  activity.append({'stage':'Cached optimisation + walk-forward','status':'CACHE_HIT','seconds':0,'backtests':0,'cache_reused':bool(cached)})
 # downstream lightweight decision outputs
 for mod in ['scripts.dca_optimisation_v2_engine','scripts.candidate_evidence_grade_engine','scripts.research_evidence_engine','scripts.research_pipeline_engine','scripts.candidate_optimisation_engine','scripts.recommended_bots_engine','scripts.coin_registry_engine','scripts.recommendation_timeline_engine','scripts.expansion_readiness_engine','scripts.research_activity_engine','scripts.portfolio_capital_manager_v2','scripts.portfolio_allocation_engine','scripts.candidate_review_engine','scripts.live_strategy_revalidation_engine','scripts.integrity_guard_engine']:
  run(mod,check=False)
 hist=load(DOCS/'historical_data_status.json');wf=load(DOCS/'kucoin_walk_forward.json');disc=load(DOCS/'coin_discovery.json')
 elapsed=round(time.monotonic()-started,2)
 prior=db.cache_get('scheduler_duration','constant') or {}
 prev=float(prior.get('seconds') or elapsed);estimate=round((prev+elapsed)/2,1);db.cache_put('scheduler_duration','constant',{'seconds':elapsed},elapsed)
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'mode':'autonomous_cached_background_research',
  'status':'HEALTHY','activity':activity,'elapsed_seconds':elapsed,'typical_cycle_seconds':estimate,
  'market_scan':{'markets_shortlisted':len(disc.get('shortlist') or []),'researched_this_scan':len(disc.get('researched_candidates') or []),'cadence_minutes':p.get('market_scan_minutes',60)},
  'history':{'ready':hist.get('research_ready_count',0),'total':hist.get('candidate_count',0),'progress_pct':hist.get('progress_pct',0)},
  'research':{'fingerprint_changed':fp!=old,'cache_hit':not research_due,'backtests_run_this_cycle':backtests,'ready_for_manual_review':(wf.get('summary') or {}).get('ready_for_manual_review',0),'next_full_revalidation_hours':p.get('full_revalidation_hours',24)},
  'database':db.write_status(),'principle':'Scan broadly, download selectively, cache aggressively, validate on unseen KuCoin data, surface only evidence-backed actions.'}
 write(payload);print(f'Research scheduler: {payload["status"]}; cache_hit={payload["research"]["cache_hit"]}; backtests={backtests}; elapsed={elapsed}s');return 0
if __name__=='__main__':raise SystemExit(main())
