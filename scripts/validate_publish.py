from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
errors=[]
for p in DOCS.glob('*.json'):
    try:
        raw=p.read_text(encoding='utf-8')
        if not raw.strip(): raise ValueError('empty file')
        json.loads(raw)
    except Exception as e: errors.append(f'{p.relative_to(ROOT)}: {e}')
refs=set()
for p in DOCS.glob('*.html'):
    txt=p.read_text(encoding='utf-8',errors='replace')
    for ref in re.findall(r'(?:href|src)=["\']([^"\']+)',txt):
        ref=ref.split('?')[0].split('#')[0]
        if not ref or ref.startswith(('http:','https:','mailto:','javascript:')): continue
        if ref.endswith(('.html','.css','.js','.json')): refs.add((p,ref))
for origin,ref in refs:
    if not (origin.parent/ref).exists(): errors.append(f'{origin.relative_to(ROOT)} -> missing {ref}')
required=['index.html','research_hub.html','research_intelligence.html','v31_2.css','v31_2.js','strategies.json','version.json']
for r in required:
    if not (DOCS/r).exists(): errors.append(f'missing required docs/{r}')
if errors:
    print('PUBLISH VALIDATION FAILED')
    print('\n'.join(' - '+e for e in errors));sys.exit(1)
print(f'Publish validation passed: {len(list(DOCS.glob("*.json")))} JSON files and {len(list(DOCS.glob("*.html")))} HTML pages checked.')
