#!/usr/bin/env python3
"""Canonical V46 source-health interpretation; age is not automatically a system fault."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'source_health.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 f=load('freshness_status.json'); comps=f.get('components') or []
 faults=[x for x in comps if x.get('status')=='ACTION_REQUIRED']; overdue=[x for x in comps if x.get('status')=='OVERDUE']
 overall='ACTION_REQUIRED' if faults else ('REFRESH_OVERDUE' if overdue else f.get('overall','CURRENT'))
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'overall':overall,'fault_count':len(faults),'overdue_count':len(overdue),'components':comps,'interpretation':'Ageing data is a refresh condition, not a system warning, unless a collector error or decision-blocking dependency exists.'}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print('Source health written:',OUT);return 0
if __name__=='__main__':raise SystemExit(main())
