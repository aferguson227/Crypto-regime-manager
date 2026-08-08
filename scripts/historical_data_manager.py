#!/usr/bin/env python3
"""V46 public KuCoin historical-data ledger and continuity planner.
Network acquisition is deliberately bounded to shortlisted research assets; it never requires private credentials.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'historical_data_status.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 disc=load('coin_discovery.json'); researched=disc.get('researched_candidates') or []; shortlist=disc.get('shortlist') or []
 symbols=[]
 for x in researched+shortlist[:20]:
  s=str(x.get('symbol') or '')
  if s and s not in symbols:symbols.append(s)
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'provider':'KuCoin public candles','private_credentials_required':False,'target_timeframe':'4hour','candidate_symbols':symbols,'candidate_count':len(symbols),'continuity_policy':'append only completed candles; deduplicate by timestamp; detect gaps before research','post_q1_gap_supported':True,'status':'READY' if symbols else 'WAITING_FOR_DISCOVERY','note':'Historical acquisition is candidate-bounded. Full parameter optimisation is not run across every listed token.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8'); print('Historical data status written:',OUT); return 0
if __name__=='__main__':raise SystemExit(main())
