#!/usr/bin/env python3
"""V61 bridge between isolated heavy research and the fast operational Local Agent."""
from __future__ import annotations
import argparse,json,os,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
FILES=[
 'coin_discovery.json','historical_data_status.json','regime_backtest_intelligence.json','kucoin_walk_forward.json',
 'adaptive_research_queue.json','candidate_evidence_grades.json','research_evidence.json','research_pipeline.json',
 'optimisation_queue.json','recommended_bots.json','coin_registry.json','recommendation_timeline.json',
 'expansion_readiness.json','research_activity.json','portfolio_allocation_recommendations.json','candidate_review.json',
 'research_scheduler_status.json','dca_optimisation_v2.json','dca_reoptimisation_queue.json','kraken_validation_evidence_status.json'
]
def root():
 raw=os.getenv('CRM_DATA_ROOT')
 base=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 p=base/'Research'/'PublishedSnapshot';p.mkdir(parents=True,exist_ok=True);return p
def export(src=DOCS):
 out=root();count=0
 for n in FILES:
  p=Path(src)/n
  if p.exists():shutil.copy2(p,out/n);count+=1
 (out/'manifest.json').write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'files':count},indent=2),encoding='utf-8')
 print(f'Research snapshot exported: {count} file(s)');return 0
def import_latest():
 src=root();count=0
 for n in FILES:
  p=src/n
  if p.exists():shutil.copy2(p,DOCS/n);count+=1
 print(f'Research snapshot imported: {count} file(s)');return 0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['export','import']);ap.add_argument('--source')
 a=ap.parse_args();return export(Path(a.source) if a.source else DOCS) if a.mode=='export' else import_latest()
if __name__=='__main__':raise SystemExit(main())
