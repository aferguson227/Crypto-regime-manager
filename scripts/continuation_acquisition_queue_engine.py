#!/usr/bin/env python3
"""V52 priority acquisition queue for unresolved Kraken-cutoff candidates."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'continuation_acquisition_queue.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 c=load('cross_exchange_continuation.json');hist=load('historical_data_status.json');hby={str(x.get('symbol') or '').split('-')[0].upper():x for x in hist.get('inventory') or []};rows=[]
 for x in c.get('assets') or []:
  if x.get('continuation_status')!='WAITING_FOR_COMPARABLE_DATA':continue
  a=str(x.get('asset') or '').upper();h=hby.get(a) or {}
  rows.append({'asset':a,'pair':f'{a}-USDT','priority':'HIGH','reason':'Frozen Kraken validation ended open and later KuCoin continuation cannot yet be resolved.',
    'kucoin_bars_available':h.get('bars',0),'kucoin_history_status':h.get('status') or 'MISSING',
    'required_action':'Prioritise KuCoin 4h history acquisition until the post-Kraken cutoff period is covered.'})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'priority_candidates':rows,
    'count':len(rows),'automatic':True}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Continuation acquisition queue: {len(rows)} priority asset(s)');return 0
if __name__=='__main__':raise SystemExit(main())
