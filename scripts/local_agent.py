#!/usr/bin/env python3
"""V41.2 local autonomous data agent.

Runs private KuCoin collection from the user's own supported-region PC, rebuilds
read-only intelligence, and publishes only material JSON changes to GitHub.
Trading/execution remains disabled.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; STATUS=DOCS/'local_agent_status.json'
MODULES=['scripts.kucoin_account_sync','scripts.capital_intelligence_engine','scripts.operating_state_engine','scripts.deployment_intelligence_engine','scripts.recommendation_intelligence_engine','scripts.portfolio_intelligence_engine','scripts.cloud_reliability_engine','scripts.operational_intelligence_engine','scripts.synchronization_engine','scripts.decision_quality_engine','scripts.engineering_intelligence_engine','scripts.command_state_engine','scripts.professional_workspace_engine','scripts.execution_provider_manager','scripts.research_evidence_engine','scripts.research_pipeline_engine']

def now(): return datetime.now(timezone.utc).isoformat()
def run(args,check=True):
    r=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
    if r.stdout: print(r.stdout,end='')
    if r.stderr: print(r.stderr,end='',file=sys.stderr)
    if check and r.returncode: raise RuntimeError('Command failed: '+' '.join(args))
    return r

def write_status(status,message,started,extra=None):
    payload={'application_version':(ROOT/'VERSION').read_text().strip(),'generated_at':now(),'started_at':started,'status':status,'message':message,'mode':'local_read_only_agent','pc_required_for_private_refresh':True,'execution_enabled':False,'write_trading_enabled':False}
    if extra: payload.update(extra)
    STATUS.write_text(json.dumps(payload,indent=2),encoding='utf-8')

def clean_generated(): run([sys.executable,'-m','scripts.generated_output_manager','clean'])
def git_clean(): return run(['git','status','--porcelain'],check=False).stdout.strip()==''

def publish_material():
    rows=run([sys.executable,'-m','scripts.material_change_manager','stage','--profile','local_agent']).stdout
    staged=run(['git','diff','--cached','--name-only'],check=False).stdout.strip().splitlines()
    if not staged:
        print('Local agent: no material changes to publish.')
        return False
    run(['git','config','user.name','crm-local-agent'])
    run(['git','config','user.email','crm-local-agent@users.noreply.github.com'])
    run(['git','commit','-m','Refresh CRM local capital intelligence'])
    for attempt in range(1,4):
        p=run(['git','push','origin','main'],check=False)
        if p.returncode==0: return True
        run(['git','fetch','origin','main'])
        run(['git','rebase','origin/main'])
        time.sleep(attempt*3)
    raise RuntimeError('Local agent could not push after three retries.')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--publish',action='store_true'); args=ap.parse_args(); started=now()
    try:
        clean_generated()
        if not git_clean():
            write_status('BLOCKED','Local repository has source changes; automatic data refresh skipped.',started)
            return 2
        run(['git','fetch','origin','main']); run(['git','pull','--rebase','origin','main'])
        for mod in MODULES: run([sys.executable,'-m',mod])
        ku=json.loads((DOCS/'kucoin_account.json').read_text(encoding='utf-8-sig'))
        status='HEALTHY' if ku.get('status')=='ok' else 'DEGRADED'
        write_status(status,'Local private-data refresh completed.' if status=='HEALTHY' else 'Local agent ran but KuCoin remains degraded.',started,{'kucoin_status':ku.get('status'),'kucoin_diagnostic':(ku.get('diagnostic') or {}).get('category')})
        run([sys.executable,'-m','scripts.validate_publish'])
        if args.publish: publish_material()
        return 0 if status=='HEALTHY' else 1
    except Exception as exc:
        write_status('ERROR',str(exc)[:300],started)
        print('Local agent error:',exc)
        return 1
if __name__=='__main__': raise SystemExit(main())
