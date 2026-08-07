#!/usr/bin/env python3
"""Diagnose and, with explicit approval, repair deterministic workflow drift."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.workflow_policy import validate
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/workflow_doctor.json';PAGES=ROOT/'.github/workflows/pages-deploy.yml'

def diagnose():
    errors=validate(); issues=[]
    for e in errors:
        fp='WORKFLOW_POLICY_DRIFT'; safe=False
        if 'Pages deploy timeout' in e: fp='PAGES_TIMEOUT_TOO_SHORT';safe=True
        elif 'Pages cancellation policy' in e: fp='PAGES_CONCURRENCY_DRIFT';safe=True
        elif 'superseded legacy workflow' in e: fp='LEGACY_WORKFLOW_PRESENT';safe=True
        issues.append({'fingerprint':fp,'detail':e,'safe_repair':safe})
    return issues

def apply(issues):
    changed=[]
    if PAGES.exists() and any(x['fingerprint'] in {'PAGES_TIMEOUT_TOO_SHORT','PAGES_CONCURRENCY_DRIFT'} for x in issues):
        s=PAGES.read_text(encoding='utf-8')
        s=re.sub(r'cancel-in-progress:\s*true','cancel-in-progress: false',s)
        m=re.search(r'(?ms)(^  deploy:\s*\n.*?^    timeout-minutes:\s*)\d+',s)
        if m:s=s[:m.start()]+m.group(1)+'30'+s[m.end():]
        PAGES.write_text(s,encoding='utf-8');changed.append(str(PAGES.relative_to(ROOT)))
    for rel in ['.github/workflows/crm-self-heal.yml','.github/workflows/engineering-audit.yml','.github/workflows/multi-coin-update.yml','.github/workflows/threecommas-update.yml']:
        p=ROOT/rel
        if p.exists() and any(x['fingerprint']=='LEGACY_WORKFLOW_PRESENT' and rel in x['detail'] for x in issues):
            p.unlink();changed.append(rel)
    return changed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply-approved',action='store_true');a=ap.parse_args();before=diagnose();changed=apply(before) if a.apply_approved else [];after=diagnose();now=datetime.now(timezone.utc).isoformat()
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'state':'HEALTHY' if not after else 'ATTENTION','issues':after,'repairs_applied':changed,'approval_model':'Workflow source repair only occurs after explicit --apply-approved invocation.','guardrails':{'no_force_push':True,'no_secret_changes':True,'no_trading_changes':True}}
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Workflow Doctor: {payload["state"]}; issues={len(after)} repairs={len(changed)}');return 0 if not after else 1
if __name__=='__main__':raise SystemExit(main())
