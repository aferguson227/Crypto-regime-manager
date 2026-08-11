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

# Release/runtime publication version policy.
# Release-owned metadata MUST equal the installed software version.
# Mutable runtime snapshots may legitimately lag after a source release; an older
# snapshot is reported as REFRESH REQUIRED but does not invalidate the software release.
policy_path=ROOT/'config'/'publication_version_policy.json'
if policy_path.exists():
    publication_policy=json.loads(policy_path.read_text(encoding='utf-8-sig'))
else:
    publication_policy={
        'release_owned':['version.json','diagnostics.json'],
        'runtime_snapshots':['system_integrity.json','operating_state.json','capital_intelligence.json',
                             'deployment_intelligence.json','recommendation_intelligence.json','outcome_intelligence.json',
                             'portfolio_intelligence.json','adaptive_intelligence.json','market_intelligence.json']
    }

def _published_version(obj):
    return obj.get('application_version') or obj.get('version') or ((obj.get('metadata') or {}).get('application_version'))

for name in publication_policy.get('release_owned') or []:
    path=DOCS/name
    if not path.exists(): continue
    try:
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        reported=_published_version(obj)
        if reported and str(reported)!=str(release['version']):
            errors.append(f'docs/{name} reports version {reported}, expected {release["version"]}')
    except Exception:
        pass

runtime_version_warnings=[]
for name in publication_policy.get('runtime_snapshots') or []:
    path=DOCS/name
    if not path.exists(): continue
    try:
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        reported=_published_version(obj)
        if reported and str(reported)!=str(release['version']):
            # A future-version runtime snapshot is contradictory and remains fatal.
            future=False
            try:
                future=tuple(int(x) for x in str(reported).split('.')) > tuple(int(x) for x in str(release['version']).split('.'))
            except Exception:
                future=False
            if future:
                errors.append(f'docs/{name} reports future runtime version {reported}, application is {release["version"]}')
            else:
                runtime_version_warnings.append((name,str(reported)))
    except Exception:
        pass

if runtime_version_warnings:
    print('RUNTIME PUBLICATION REFRESH REQUIRED')
    for name,reported in runtime_version_warnings:
        print(f' - docs/{name} snapshot={reported}; application={release["version"]} (does not invalidate source release)')

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
