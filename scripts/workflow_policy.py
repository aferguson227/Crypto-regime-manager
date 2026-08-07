#!/usr/bin/env python3
"""Canonical workflow contract validator for CRM V39.1.

The validator treats all workflows as one coordinated automation system and
ensures only the Pages workflow can deploy Pages. It never mutates workflows.
"""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config/workflow_policy.json'

def load_policy():
    return json.loads(POLICY.read_text(encoding='utf-8-sig'))

def _text(rel:str)->str:
    p=ROOT/rel
    return p.read_text(encoding='utf-8') if p.exists() else ''

def validate()->list[str]:
    p=load_policy(); errors=[]; groups={}; publishers=[]
    workflows=p.get('workflows') or {}
    for key,item in workflows.items():
        rel=item['path']; path=ROOT/rel
        if not path.exists():
            errors.append(f'{rel}: missing'); continue
        text=path.read_text(encoding='utf-8')
        if 'workflow_dispatch:' not in text:
            errors.append(f'{rel}: missing manual recovery trigger')
        grp=item.get('concurrency_group')
        if grp:
            if f'group: {grp}' not in text: errors.append(f'{rel}: wrong concurrency group')
            if grp in groups: errors.append(f'{rel}: concurrency group also used by {groups[grp]}')
            groups[grp]=rel
        if re.search(r'run:\s*python\s+scripts[/\\][^\s]+\.py',text):
            errors.append(f'{rel}: use python -m package execution')
        if 'actions/deploy-pages@' in text:
            publishers.append(rel)
            if key!='pages': errors.append(f'{rel}: only Pages workflow may deploy Pages')
        if item.get('schedule') and item['schedule'] not in text:
            errors.append(f'{rel}: missing approved schedule {item["schedule"]}')
        for mod in item.get('required_modules') or []:
            if mod not in text: errors.append(f'{rel}: missing required module {mod}')
    if p.get('guardrails',{}).get('single_pages_publisher') and len(publishers)!=1:
        errors.append(f'Expected one Pages publisher; found {len(publishers)}: {publishers}')
    pages=workflows.get('pages') or {}; text=_text(pages.get('path',''))
    for needle,label in [
        (pages.get('artifact_action'),'Pages artifact action'),
        (pages.get('deploy_action'),'Pages deploy action'),
        (f"cancel-in-progress: {str(pages.get('cancel_in_progress')).lower()}",'Pages cancellation policy'),
        (f"timeout-minutes: {pages.get('deploy_timeout_minutes')}",'Pages deploy timeout'),
        (f"path: {pages.get('publish_path')}",'Pages publication path')]:
        if needle and needle not in text: errors.append(f'{pages.get("path")}: invalid {label}')
    for rel in p.get('forbidden_legacy_workflows') or []:
        if (ROOT/rel).exists(): errors.append(f'{rel}: superseded legacy workflow must be removed')
    return errors

def main()->int:
    errors=validate()
    if errors:
        print('WORKFLOW POLICY VALIDATION FAILED')
        for e in errors: print(' -',e)
        return 1
    print('Workflow policy valid: four isolated CRM workflows with one queue-safe Pages publisher.')
    return 0
if __name__=='__main__': raise SystemExit(main())
