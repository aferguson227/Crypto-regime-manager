#!/usr/bin/env python3
"""V56 priority acquisition and progress for unresolved Kraken-cutoff candidates."""
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
 c=load('cross_exchange_continuation.json');hist=load('historical_data_status.json')
 hby={str(x.get('symbol') or '').split('-')[0].upper():x for x in hist.get('inventory') or []};rows=[]
 for x in c.get('assets') or []:
  state=str(x.get('continuation_status') or '')
  unresolved={'WAITING_FOR_COMPARABLE_DATA','KRAKEN_EVIDENCE_MATERIALISING','KUCOIN_HISTORY_ACQUIRING','KUCOIN_HISTORY_DOES_NOT_REACH_CUTOFF','KUCOIN_CONTINUATION_GAP'}
  if state not in unresolved:continue
  a=str(x.get('asset') or '').upper();h=hby.get(a) or {};bars=int(h.get('bars') or 0)
  pages=h.get('estimated_pages_remaining');cycles=None if pages is None else max(1,(int(pages)+4)//5)
  reason=str(x.get('reason') or ('Kraken validation source is being materialised.' if state=='KRAKEN_EVIDENCE_MATERIALISING' else
          'KuCoin 4-hour continuation history is being acquired automatically.' if not x.get('kucoin_file_exists',False) else
          'KuCoin history does not yet provide directly comparable post-cutoff coverage.'))
  queue_state='MATERIALISING_KRAKEN_EVIDENCE' if state=='KRAKEN_EVIDENCE_MATERIALISING' else 'DOWNLOADING_CONTINUATION_HISTORY'
  rows.append({'asset':a,'pair':f'{a}-USDT','priority':'HIGH','state':queue_state,'continuation_status':state,
   'reason':reason,'kraken_cutoff':x.get('kraken_cutoff'),'kucoin_bars_available':bars,'kucoin_history_start':h.get('earliest') or h.get('start'),
   'kucoin_history_end':h.get('latest') or h.get('end'),'kucoin_history_status':h.get('status') or 'MISSING',
   'estimated_pages_remaining':pages,'estimated_background_cycles_remaining':cycles,'expected_cycle_minutes':15,
   'estimated_minutes_remaining':cycles*15 if cycles is not None else None,'automatic':True,
   'required_action':'No manual action normally required. CRM prioritises this asset until post-cutoff KuCoin history is available.'})
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
          'priority_candidates':rows,'count':len(rows),'automatic':True,
          'explanation':'Continuation history is acquired automatically in bounded background batches so dashboard refreshes are not blocked.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Continuation acquisition queue: {len(rows)} priority asset(s)');return 0
if __name__=='__main__':raise SystemExit(main())
