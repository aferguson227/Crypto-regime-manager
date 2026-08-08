#!/usr/bin/env python3
"""V49 installer Git-state recovery guard.

Auto-recovers interrupted operations only when every unmerged path is declared
generated runtime state. Source-code conflicts always stop for manual review.
"""
from __future__ import annotations
import argparse,json,subprocess
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args,check=False):
 return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)
def policy(path=None):
 p=Path(path) if path else ROOT/'config'/'generated_outputs_policy.json'
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except:return {}
def unmerged():
 r=run(['git','diff','--name-only','--diff-filter=U'])
 return [x.strip().replace('\\','/') for x in r.stdout.splitlines() if x.strip()]
def operation():
 g=ROOT/'.git'
 if (g/'rebase-merge').exists() or (g/'rebase-apply').exists():return 'rebase'
 if (g/'MERGE_HEAD').exists():return 'merge'
 if (g/'CHERRY_PICK_HEAD').exists():return 'cherry-pick'
 return None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--policy');ap.add_argument('--recover',action='store_true');a=ap.parse_args()
 op=operation();paths=unmerged();cfg=policy(a.policy);runtime=set(cfg.get('runtime_generated_patterns') or [])
 source=[p for p in paths if p not in runtime]
 state='CLEAN' if not op and not paths else ('RUNTIME_CONFLICT_RECOVERABLE' if paths and not source else 'SOURCE_CONFLICT_MANUAL')
 print(f'Git state: {state}; operation={op or "none"}; unmerged={len(paths)}')
 if source:print('Source/unclassified conflicts:',', '.join(source))
 if not a.recover:return 0 if state!='SOURCE_CONFLICT_MANUAL' else 2
 if state=='CLEAN':return 0
 if state=='SOURCE_CONFLICT_MANUAL':return 2
 # Safety ref points to current original branch/commit before abort/reset.
 head=run(['git','rev-parse','ORIG_HEAD']).stdout.strip() or run(['git','rev-parse','HEAD']).stdout.strip()
 if head:
  name='recovery-before-v49-'+datetime.now().strftime('%Y%m%d-%H%M%S')
  run(['git','branch',name,head]);print('Safety branch:',name)
 if op=='rebase':run(['git','rebase','--abort'])
 elif op=='merge':run(['git','merge','--abort'])
 elif op=='cherry-pick':run(['git','cherry-pick','--abort'])
 run(['git','fetch','origin','main'])
 run(['git','reset','--hard','origin/main'])
 print('Runtime-only interrupted Git operation recovered safely.')
 return 0
if __name__=='__main__':raise SystemExit(main())
