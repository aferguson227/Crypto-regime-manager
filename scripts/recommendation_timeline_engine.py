#!/usr/bin/env python3
"""V44 combined live recommendation/candidate lifecycle timeline."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'recommendation_timeline.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
 except:return {}
def main():
 hist=load('recommendation_history.json'); registry=load('coin_registry.json'); old=load('recommendation_timeline.json'); events=old.get('events') if isinstance(old.get('events'),list) else []
 ids={e.get('event_id') for e in events if isinstance(e,dict)}
 for r in hist.get('records') or []:
  if not isinstance(r,dict):continue
  seed={'kind':'BOT_RECOMMENDATION','id':r.get('recommendation_id')}; eid=hashlib.sha256(json.dumps(seed,sort_keys=True).encode()).hexdigest()[:24]
  if eid not in ids:events.append({'event_id':eid,'recorded_at':r.get('recorded_at'),'kind':'BOT_RECOMMENDATION','asset':r.get('asset'),'status':r.get('action'),'confidence_pct':r.get('overall_confidence'),'outcome':r.get('outcome')});ids.add(eid)
 for c in registry.get('coins') or []:
  seed={'kind':'COIN_STATUS','asset':c.get('asset'),'status':c.get('status'),'rec':c.get('current_recommendation')};eid=hashlib.sha256(json.dumps(seed,sort_keys=True).encode()).hexdigest()[:24]
  if eid not in ids:events.append({'event_id':eid,'recorded_at':registry.get('generated_at'),'kind':'COIN_STATUS','asset':c.get('asset'),'status':c.get('status'),'confidence_pct':c.get('recommendation_confidence_pct'),'detail':'; '.join(c.get('reasons') or [])[:300]});ids.add(eid)
 events=events[-1000:]
 OUT.write_text(json.dumps({'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'events':events,'event_count':len(events),'live_updating':True},indent=2),encoding='utf-8'); print(f'Recommendation timeline written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
