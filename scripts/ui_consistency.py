#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';POLICY=ROOT/'config/page_policy.json';MOJIBAKE=('â€”','â€“','Â£','â†’','ï¿½')
def main():
 errors=[];p=json.loads(POLICY.read_text(encoding='utf-8-sig'));canonical={x['path'] for x in p.get('canonical_pages',[])};current=application_version()
 for name in canonical:
  f=DOCS/name
  if not f.exists():errors.append(f'{name}: canonical page missing');continue
  text=f.read_text(encoding='utf-8-sig')
  if 'design-system.css' not in text:errors.append(f'{name}: missing shared design CSS')
  if 'design-system.js' not in text:errors.append(f'{name}: missing shared navigation/formatting JS')
  if 'name="viewport"' not in text:errors.append(f'{name}: responsive viewport missing')
  if any(x in text for x in ('workspace-nav','v20-nav','v20-tools')):errors.append(f'{name}: legacy navigation markup remains')
  visible=re.findall(r'>\s*V(\d+\.\d+\.\d+)(?=\s|<|·)',text);stale=[v for v in visible if v!=current]
  if stale:errors.append(f'{name}: stale visible version labels {stale}')
  for bad in MOJIBAKE:
   if bad in text:errors.append(f'{name}: mojibake {bad!r}')
 js=(DOCS/'design-system.js').read_text(encoding='utf-8')
 if 'crm-global-nav' not in js:errors.append('design-system.js: canonical navigation missing')
 if 'workspace-nav,.v20-nav,.v20-tools' not in js:errors.append('design-system.js: legacy navigation suppression missing')
 pjs=(DOCS/'portfolio.js').read_text(encoding='utf-8')
 if "style:'currency'" in pjs:errors.append('portfolio.js: dollar currency formatting remains')
 if 'CRMFormat.quote' not in pjs:errors.append('portfolio.js: explicit quote currency formatter missing')
 if errors:
  print('UI CONSISTENCY VALIDATION FAILED');[print(' -',e) for e in errors];return 1
 print(f'UI consistency valid: {len(canonical)} canonical pages use one navigation, current version labels and explicit asset/quote formatting.');return 0
if __name__=='__main__':raise SystemExit(main())