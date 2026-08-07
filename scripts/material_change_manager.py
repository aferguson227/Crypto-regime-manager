#!/usr/bin/env python3
"""Semantic material-change staging for quiet CRM automation.

Compares generated files with HEAD while ignoring approved volatile timestamp keys.
Used by health automation so timestamp-only refreshes do not create commits or Pages deploys.
"""
from __future__ import annotations
import argparse,fnmatch,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config/material_change_policy.json'

def policy(): return json.loads(POLICY.read_text(encoding='utf-8-sig'))
def git_show(rel):
 r=subprocess.run(['git','show',f'HEAD:{rel}'],cwd=ROOT,text=True,capture_output=True)
 return r.stdout if r.returncode==0 else None

def normalize(value,volatile):
 if isinstance(value,dict): return {k:normalize(v,volatile) for k,v in sorted(value.items()) if k not in volatile}
 if isinstance(value,list): return [normalize(v,volatile) for v in value]
 return value

def semantic_text(text,rel,volatile):
 if rel.lower().endswith('.json'):
  try:return json.dumps(normalize(json.loads(text),volatile),sort_keys=True,separators=(',',':'))
  except Exception:return text.replace('\r\n','\n').strip()
 return text.replace('\r\n','\n').strip()

def expand(patterns):
 out=[]
 for pattern in patterns:
  if any(c in pattern for c in '*?['):
   out.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in ROOT.glob(pattern) if p.is_file())
  elif (ROOT/pattern).is_file(): out.append(pattern)
 return sorted(dict.fromkeys(out))

def meaningful(profile='health'):
 p=policy(); spec=(p.get('profiles') or {}).get(profile) or {}; volatile=set(p.get('volatile_keys') or [])
 excluded=set(expand(spec.get('exclude') or [])); rows=[]
 for rel in expand(spec.get('paths') or []):
  if rel in excluded: continue
  current=(ROOT/rel).read_text(encoding='utf-8-sig',errors='replace'); base=git_show(rel)
  if base is None or semantic_text(current,rel,volatile)!=semantic_text(base,rel,volatile): rows.append(rel)
 return rows

def stage(profile='health'):
 rows=meaningful(profile)
 if rows: subprocess.run(['git','add','--',*rows],cwd=ROOT,check=True)
 return rows

def validate():
 p=policy(); assert p.get('profiles',{}).get('health'); assert 'generated_at' in p.get('volatile_keys',[])
 print('Material-change policy valid: volatile timestamps are ignored for health publication.'); return 0

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['validate','list','stage'],nargs='?',default='validate'); ap.add_argument('--profile',default='health'); a=ap.parse_args()
 if a.action=='validate': return validate()
 rows=stage(a.profile) if a.action=='stage' else meaningful(a.profile)
 for x in rows: print(x)
 print(f'Material changes: {len(rows)}')
 return 0
if __name__=='__main__': raise SystemExit(main())
