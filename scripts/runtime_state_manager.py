#!/usr/bin/env python3
r"""CRM Runtime State Separation 1.0.

Separates continuously changing operational state from the Git working tree.

Authoritative live/runtime state:
    C:\Crypto\CRM_Data\Runtime\State

Isolated resident-service application mirror:
    C:\Crypto\CRM_Data\Runtime\App

Git-tracked docs/*.json becomes a controlled publication snapshot only.

This manager never changes trading/execution permissions.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config'/'generated_outputs_policy.json'

def runtime_base():
 raw=os.getenv('CRM_DATA_ROOT')
 base=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 return base/'Runtime'
def state_dir(): return runtime_base()/'State'
def app_dir(): return runtime_base()/'App'

def policy(root=ROOT):
 p=Path(root)/'config'/'generated_outputs_policy.json'
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except:return {'runtime_generated_patterns':[]}

def runtime_relpaths(root=ROOT):
 return list(dict.fromkeys(policy(root).get('runtime_generated_patterns') or []))

def atomic_copy(src:Path,dst:Path):
 dst.parent.mkdir(parents=True,exist_ok=True)
 tmp=dst.with_name(dst.name+'.tmp')
 shutil.copy2(src,tmp)
 os.replace(tmp,dst)

def capture(source_root:Path):
 """Copy runtime outputs from an application tree into external authoritative State."""
 sdir=state_dir();sdir.mkdir(parents=True,exist_ok=True);count=0
 for rel in runtime_relpaths(source_root):
  p=source_root/rel
  if p.is_file():
   atomic_copy(p,sdir/Path(rel).name);count+=1
 meta={'captured_at':time.time(),'source':str(source_root),'count':count}
 (sdir/'runtime_state_meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 return count

def import_state(target_root:Path):
 """Overlay external runtime state into an application tree for one controlled cycle."""
 sdir=state_dir();count=0
 for rel in runtime_relpaths(target_root):
  src=sdir/Path(rel).name
  dst=target_root/rel
  if src.is_file():
   atomic_copy(src,dst);count+=1
 return count

def seed_from_project():
 """Initialise State from the latest published Git snapshot without overwriting newer State."""
 sdir=state_dir();sdir.mkdir(parents=True,exist_ok=True);count=0
 for rel in runtime_relpaths(ROOT):
  src=ROOT/rel;dst=sdir/Path(rel).name
  if src.is_file() and not dst.exists():
   atomic_copy(src,dst);count+=1
 return count

def ignore_copy(directory,names):
 blocked={'.git','__pycache__','.pytest_cache','diagnostics_logs','diagnostics_exports','engineering_exports',
          'hotfix_backups','.fix-backups'}
 return {n for n in names if n in blocked}

def prepare_app():
 """Refresh code/static files in isolated runtime App while preserving runtime State."""
 base=runtime_base();base.mkdir(parents=True,exist_ok=True)
 target=app_dir();tmp=base/'App.new'
 shutil.rmtree(tmp,ignore_errors=True)
 shutil.copytree(ROOT,tmp,ignore=ignore_copy)
 # Runtime values in the copied docs are only a seed; authoritative external State wins.
 seed_from_project()
 import_state(tmp)
 old=base/'App.old';shutil.rmtree(old,ignore_errors=True)
 if target.exists(): target.replace(old)
 tmp.replace(target)
 shutil.rmtree(old,ignore_errors=True)
 return target

def publish_to_project():
 """Controlled publication: external State -> Git working tree docs snapshot."""
 sdir=state_dir();count=0
 for rel in runtime_relpaths(ROOT):
  src=sdir/Path(rel).name
  dst=ROOT/rel
  if src.is_file():
   atomic_copy(src,dst);count+=1
 return count

def status():
 sdir=state_dir();app=app_dir()
 available=sum((sdir/Path(x).name).is_file() for x in runtime_relpaths(ROOT))
 return {'runtime_base':str(runtime_base()),'state_dir':str(sdir),'app_dir':str(app),
         'state_files':available,'policy_files':len(runtime_relpaths(ROOT)),
         'app_ready':app.exists(),'git_docs_are_publication_snapshot':True}

def main():
 ap=argparse.ArgumentParser()
 sub=ap.add_subparsers(dest='cmd',required=True)
 sub.add_parser('prepare')
 sub.add_parser('seed')
 sub.add_parser('capture')
 sub.add_parser('import')
 sub.add_parser('publish')
 sub.add_parser('status')
 a=ap.parse_args()
 if a.cmd=='prepare':
  p=prepare_app();print(f'Runtime application prepared: {p}');return 0
 if a.cmd=='seed':
  print(f'Runtime state seeded: {seed_from_project()} file(s)');return 0
 if a.cmd=='capture':
  print(f'Runtime state captured: {capture(ROOT)} file(s)');return 0
 if a.cmd=='import':
  print(f'Runtime state imported: {import_state(ROOT)} file(s)');return 0
 if a.cmd=='publish':
  print(f'Runtime publication snapshot written: {publish_to_project()} file(s)');return 0
 if a.cmd=='status':
  print(json.dumps(status(),indent=2));return 0
 return 2
if __name__=='__main__':raise SystemExit(main())
