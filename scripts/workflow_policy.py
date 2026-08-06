#!/usr/bin/env python3
"""Canonical GitHub workflow contract validator for CRM V35."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config/workflow_policy.json'

def validate()->list[str]:
    p=json.loads(POLICY.read_text(encoding='utf-8'))
    errors=[]
    pub=ROOT/p['publisher_workflow']
    if not pub.exists(): return [f"Missing publisher workflow: {pub.relative_to(ROOT)}"]
    text=pub.read_text(encoding='utf-8')
    expected=p['publisher']
    checks=[
      (expected['artifact_action'], 'missing Pages artifact action'),
      (expected['deploy_action'], 'missing Pages deploy action'),
      (f"needs: {expected['needs']}", 'deploy job not linked to build'),
      (f"group: {expected['concurrency_group']}", 'wrong Pages concurrency group'),
      (f"cancel-in-progress: {str(expected['cancel_in_progress']).lower()}", 'wrong cancellation policy'),
      (f"timeout-minutes: {expected['deploy_timeout_minutes']}", 'wrong Pages deploy timeout'),
      (f"path: {expected['publish_path']}", 'wrong Pages publication path'),
    ]
    for needle,msg in checks:
        if needle not in text: errors.append(f"{pub.relative_to(ROOT)}: {msg}")
    for item in p['data_workflows']:
        path=ROOT/item['path']
        if not path.exists(): errors.append(f"{item['path']}: missing"); continue
        body=path.read_text(encoding='utf-8')
        for needle,label in [(item['module'],'module execution'),(item['cron'],'schedule'),('workflow_dispatch:','manual recovery trigger')]:
            if needle not in body: errors.append(f"{item['path']}: missing {label}")
        for forbidden in p['forbidden_in_data_workflows']:
            if forbidden in body: errors.append(f"{item['path']}: data workflow must not deploy Pages")
        if re.search(r'run:\s*python\s+scripts/[^\s]+\.py',body): errors.append(f"{item['path']}: use python -m package execution")
    return errors

def main()->int:
    errors=validate()
    if errors:
        print('WORKFLOW POLICY VALIDATION FAILED')
        for e in errors: print(' -',e)
        return 1
    print('Workflow policy valid: single queue-safe Pages publisher and isolated data workflows.')
    return 0
if __name__=='__main__': raise SystemExit(main())
