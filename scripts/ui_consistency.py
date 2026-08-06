#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'
MOJIBAKE=('â€”','â€“','Â£','â†’','ï¿½')
def main():
 errors=[]; pages=sorted(DOCS.glob('*.html'))
 for p in pages:
  text=p.read_text(encoding='utf-8')
  if 'design-system.css' not in text: errors.append(f'{p.name}: missing shared design CSS')
  if 'design-system.js' not in text: errors.append(f'{p.name}: missing shared navigation/formatting JS')
  if not any(x in text for x in ('index.html','Dashboard','design-system.js')): errors.append(f'{p.name}: no Dashboard return path')
  for bad in MOJIBAKE:
   if bad in text: errors.append(f'{p.name}: mojibake {bad!r}')
 js=(DOCS/'professional_workspace.js').read_text(encoding='utf-8')
 if "USDT')=>" not in js and 'CRMFormat.quote' not in js: errors.append('professional_workspace.js: quote currency formatter missing')
 engine=(ROOT/'scripts/professional_workspace_engine.py').read_text(encoding='utf-8')
 for phrase in ('currency_policy','unknown_policy','negative_sign'):
  if phrase not in engine: errors.append(f'professional_workspace_engine.py: missing {phrase}')
 if errors:
  print('UI CONSISTENCY VALIDATION FAILED'); [print(' -',e) for e in errors]; return 1
 print(f'UI consistency valid: {len(pages)} pages share navigation, design and formatting policy.')
 return 0
if __name__=='__main__': raise SystemExit(main())
