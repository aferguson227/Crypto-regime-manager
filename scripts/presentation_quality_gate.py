#!/usr/bin/env python3
"""V51 presentation quality gate across all published pages/scripts."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'presentation_quality.json'
RAW=re.compile(r'\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b')
def main():
 issues=[];htmls=sorted(DOCS.glob('*.html'));scripts=[DOCS/'design-system.js',DOCS/'unified_dashboard.js']
 ds=(DOCS/'design-system.js').read_text(encoding='utf-8')
 if 'universal presentation adapter' not in ds or 'MutationObserver' not in ds:issues.append('Universal DOM presentation adapter is missing.')
 if 'CRMFormat.label' not in ds:issues.append('Canonical label formatter is missing.')
 for path in htmls:
  text=path.read_text(encoding='utf-8',errors='ignore')
  for m in RAW.findall(text):
   # Static HTML raw enums are never acceptable outside script/code blocks; canonical pages are simple enough for this release gate.
   if m not in {'UTF_8'}:issues.append(f'{path.name}: raw machine enum {m}')
 js=(DOCS/'unified_dashboard.js').read_text(encoding='utf-8')
 for bad in ['esc(accounting.realised_profit_status','esc(g.state)','esc(c.kucoin_walk_forward_status']:
  if bad in js:issues.append('Known raw internal status may bypass formatter: '+bad)
 css=(DOCS/'design-system.css').read_text(encoding='utf-8')
 if '@media(max-width:600px)' not in css:issues.append('Mobile presentation rule missing.')
 if 'id="crm-activity"' not in (DOCS/'index.html').read_text(encoding='utf-8'):issues.append('CRM activity strip missing.')
 result='HEALTHY' if not issues else 'ATTENTION'
 payload={'schema_version':'2.0','application_version':(ROOT/'VERSION').read_text().strip(),'result':result,'issue_count':len(issues),'pages_checked':len(htmls),'issues':issues[:100],
  'checks':['universal raw-enum barrier','canonical label formatter','mobile responsive rules','activity visibility','known direct-enum leaks']}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Presentation quality: {result}; pages={len(htmls)} issues={len(issues)}');return 0 if not issues else 1
if __name__=='__main__':raise SystemExit(main())
