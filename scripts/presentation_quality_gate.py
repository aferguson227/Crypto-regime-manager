#!/usr/bin/env python3
"""V49 canonical presentation-quality gate."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'presentation_quality.json'
def main():
 issues=[]
 js=(DOCS/'unified_dashboard.js').read_text(encoding='utf-8')
 html=(DOCS/'index.html').read_text(encoding='utf-8')
 css=(DOCS/'design-system.css').read_text(encoding='utf-8')
 for bad in ['esc(accounting.realised_profit_status','esc(g.state)','esc(c.kucoin_walk_forward_status']:
  if bad in js:issues.append('Raw internal status may be visible: '+bad)
 if "replaceAll('_',' ')" not in js and 'replaceAll("_"," ")' not in js:
  issues.append('Universal enum label formatter is missing.')
 if '@media(max-width:600px)' not in css:issues.append('Mobile presentation rule missing.')
 if 'id="crm-activity"' not in html:issues.append('CRM activity strip missing.')
 if 'Review candidate' not in js:issues.append('Candidate review action missing.')
 if 'ageText=' not in js:issues.append('Canonical relative-time formatter missing.')
 result='HEALTHY' if not issues else 'ATTENTION'
 p={'schema_version':'1.0','application_version':(ROOT/'VERSION').read_text().strip(),'result':result,'issue_count':len(issues),'issues':issues,'checks':['no known raw enum leakage','mobile responsive rules','activity visibility','status formatting','canonical timestamps','candidate review workflow']}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8')
 print(f'Presentation quality: {result}; issues={len(issues)}')
 return 0 if not issues else 1
if __name__=='__main__':raise SystemExit(main())
