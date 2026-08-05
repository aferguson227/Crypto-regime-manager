from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; errors=[]
release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
if (ROOT/'VERSION').read_text().strip()!=release['version']: errors.append('VERSION disagrees with app/release.json')
for p in DOCS.glob('*.json'):
    try:
        raw=p.read_text(encoding='utf-8');
        if not raw.strip(): raise ValueError('empty file')
        json.loads(raw)
    except Exception as e: errors.append(f'{p.relative_to(ROOT)}: {e}')
refs=set()
for p in DOCS.glob('*.html'):
    txt=p.read_text(encoding='utf-8',errors='replace')
    if 'â€™' in txt or 'Â·' in txt: errors.append(f'{p.relative_to(ROOT)} contains broken UTF-8 text')
    for ref in re.findall(r'(?:href|src)=["\']([^"\']+)',txt):
        ref=ref.split('?')[0].split('#')[0]
        if not ref or ref.startswith(('http:','https:','mailto:','javascript:')): continue
        if ref.endswith(('.html','.css','.js','.json')): refs.add((p,ref))
for origin,ref in refs:
    if not (origin.parent/ref).exists(): errors.append(f'{origin.relative_to(ROOT)} -> missing {ref}')
for r in ['index.html','research_hub.html','research_intelligence.html','v31_2.css','v31_2.js','strategies.json','version.json','system_integrity.json','configuration_reconciliation.json','diagnostics.json','diagnostics.html']:
    if not (DOCS/r).exists(): errors.append(f'missing required docs/{r}')
routes=json.loads((ROOT/'config/routes.json').read_text())['routes']
for route in routes:
    if not (DOCS/route['path']).exists(): errors.append(f"route manifest missing docs/{route['path']}")
# Static safety scan: no mutation verbs/endpoints or secret material in published output.
for p in list((ROOT/'scripts/integrations').glob('*.py'))+list(DOCS.glob('*')):
    if not p.is_file(): continue
    text=p.read_text(encoding='utf-8',errors='ignore')
    if p.parent.name=='integrations' and re.search(r'urlopen\([^\n]*method\s*=\s*["\'](?:POST|PUT|PATCH|DELETE)',text,re.I): errors.append(f'{p}: write-capable HTTP method detected')
    if p.parent==DOCS and re.search(r'(BEGIN (?:RSA )?PRIVATE KEY|THREECOMMAS_RSA_PRIVATE_KEY|Apikey["\']?\s*:|bot[_ -]?control.*@)',text,re.I): errors.append(f'{p}: secret-like material detected')
if (ROOT/'data/scripts').exists() or (ROOT/'data/.github').exists(): errors.append('duplicate executable tree remains under data/')
if errors:
    print('PUBLISH VALIDATION FAILED'); print('\n'.join(' - '+e for e in errors));sys.exit(1)
print(f'Publish validation passed for V{release["version"]}: {len(list(DOCS.glob("*.json")))} JSON files and {len(list(DOCS.glob("*.html")))} HTML pages checked.')
