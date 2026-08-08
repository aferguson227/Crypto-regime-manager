#!/usr/bin/env python3
"""V45 concise Dashboard summary of background research activity."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'research_activity.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return v if isinstance(v,dict) else {}
 except:return {}
def main():
 rb=load('regime_backtest_intelligence.json');oq=load('optimisation_queue.json');rp=load('research_pipeline.json');hist=load('historical_data_status.json');kw=load('kucoin_walk_forward.json');sched=load('research_scheduler_status.json');db=load('research_database_status.json');items=oq.get('items') or []
 states={}
 for x in items:states[x.get('status')]=states.get(x.get('status'),0)+1
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'status':'ACTIVE','automatic':True,'research_cycle_hours':24,
  'summary':{'historical_symbols':hist.get('candidate_count',0),'historical_ready':hist.get('research_ready_count',0),'history_progress_pct':hist.get('progress_pct',0),'kucoin_walk_forward_ready':(kw.get('summary') or {}).get('ready_for_manual_review',0),'candidates_under_review':len(items),'regime_research_complete':states.get('REGIME_RESEARCH_COMPLETE',0),'optimisation_pending':states.get('INDEPENDENT_BASELINE_PASS_REGIME_RESEARCH_PENDING',0),'rejected':states.get('REJECTED',0),'backtests_last_cycle':(rb.get('summary') or {}).get('backtests_run',0),'datasets_last_cycle':(rb.get('summary') or {}).get('datasets',0)},
  'entry_trigger_families':rb.get('entry_trigger_families') or [],'trade_duration_policy':rb.get('trade_duration_policy') or {},'last_full_research_at':rb.get('generated_at'),'independent_walk_forward':rb.get('independent_walk_forward') or {},
  'persistent_research':{'database_status':db.get('status'),'known_assets':db.get('known_assets',0),'cached_results':db.get('cached_results',0),'scheduler_cache_hit':(sched.get('research') or {}).get('cache_hit')},'data_acquisition':{'status':hist.get('status'),'mode':hist.get('mode'),'progress_pct':hist.get('progress_pct'),'inventory':hist.get('inventory') or []},'kucoin_walk_forward':kw.get('summary') or {},'process':['Scan KuCoin USDT universe','Acquire/backfill KuCoin 4h history','Discover candidates','Classify regime','Test entry triggers','Optimise DCA settings','Penalise drawdown and capital lock','Freeze training winner','Validate independently','Confirm current KuCoin/global regime','Surface manual deployment candidate'],
  'items':[{'asset':x.get('asset'),'status':x.get('status'),'current_regime':x.get('current_regime_family'),'next_action':x.get('next_action')} for x in items]}
 payload['snapshot_id']=hashlib.sha256(json.dumps(payload['summary'],sort_keys=True).encode()).hexdigest()[:24];OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Research activity written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
