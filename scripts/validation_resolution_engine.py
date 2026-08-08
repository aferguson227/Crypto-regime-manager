#!/usr/bin/env python3
"""Preserve frozen validation cut-offs while separately tracking unresolved-position resolution."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'validation_resolution.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 wf=load('walk_forward_registry.json'); rows=[]
 for c in wf.get('coins') or []:
  q=(c.get('q1_2026_metrics') or {}); open_flag=bool(q.get('open_position') or q.get('ended_open') or q.get('open_trade'))
  if open_flag: rows.append({'asset':c.get('symbol'),'validation_cutoff_state':'OPEN','original_validation_preserved':True,'post_validation_resolution':'PENDING_CONTINUATION_DATA','note':'Later candles may resolve this frozen trade, but never rewrite the Q1 validation result.'})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'open_validation_positions':len(rows),'positions':rows,'integrity_rule':'post-validation outcomes are reported separately and cannot alter frozen validation metrics'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8'); print('Validation resolution written:',OUT);return 0
if __name__=='__main__':raise SystemExit(main())
