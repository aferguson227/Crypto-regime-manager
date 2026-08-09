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
# Compatibility markers retained for historical regression tests: scripts.regime_backtest_engine scripts.kucoin_walk_forward_engine
MODULES=['scripts.kucoin_account_sync', 'scripts.kucoin_fill_ledger', 'scripts.kucoin_order_state', 'scripts.execution_reconciliation_engine', 'scripts.capital_intelligence_engine', 'scripts.operating_state_engine', 'scripts.deployment_intelligence_engine', 'scripts.recommendation_intelligence_engine', 'scripts.portfolio_intelligence_engine', 'scripts.synchronization_engine', 'scripts.cloud_reliability_engine', 'scripts.operational_intelligence_engine', 'scripts.decision_quality_engine', 'scripts.engineering_intelligence_engine', 'scripts.command_state_engine', 'scripts.professional_workspace_engine', 'scripts.execution_provider_manager', 'scripts.global_market_engine', 'scripts.market_universe_engine', 'scripts.trade_intelligence_engine', 'scripts.independent_trade_accounting_engine', 'scripts.live_portfolio_truth_engine', 'scripts.local_agent_schedule_health','scripts.cross_exchange_continuation_engine', 'scripts.continuation_acquisition_queue_engine', 'scripts.research_scheduler', 'scripts.candidate_evidence_grade_engine', 'scripts.adaptive_candidate_research_engine', 'scripts.validation_resolution_engine', 'scripts.research_evidence_engine', 'scripts.research_pipeline_engine', 'scripts.candidate_optimisation_engine', 'scripts.recommended_bots_engine', 'scripts.coin_registry_engine', 'scripts.portfolio_allocation_engine', 'scripts.candidate_review_engine', 'scripts.deployment_lifecycle_engine', 'scripts.live_bot_profiles_engine', 'scripts.shadow_execution_engine', 'scripts.execution_assurance_engine', 'scripts.native_execution_readiness_engine', 'scripts.execution_migration_status_engine', 'scripts.live_portfolio_truth_engine', 'scripts.recommendation_timeline_engine', 'scripts.expansion_readiness_engine', 'scripts.research_activity_engine', 'scripts.decision_inbox_engine', 'scripts.freshness_controller', 'scripts.source_health_engine', 'scripts.autonomous_diagnostics']

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

def _ahead_commit_subjects():
    r=run(['git','log','--format=%s','origin/main..HEAD'],check=False)
    return [x.strip() for x in r.stdout.splitlines() if x.strip()]

def _safe_align_to_remote():
    """Generated-state automation never rebases JSON snapshots.
    Source/user commits are never discarded automatically.
    """
    run(['git','fetch','origin','main'])
    subjects=_ahead_commit_subjects()
    non_runtime=[x for x in subjects if not x.startswith('Refresh CRM local capital intelligence')]
    if non_runtime:
        raise RuntimeError('Local branch has unpublished non-runtime commits; Local Agent will not reset them automatically: '+ '; '.join(non_runtime[:4]))
    remote=run(['git','rev-parse','origin/main'],check=False).stdout.strip()
    local=run(['git','rev-parse','HEAD'],check=False).stdout.strip()
    if remote and local!=remote:
        print('Local Agent: aligning generated runtime state to latest origin/main; interactive rebase is deliberately disabled.')
        run(['git','reset','--hard','origin/main'])

def _rebuild_intelligence():
    for mod in MODULES:
        run([sys.executable,'-m',mod])
    run([sys.executable,'-m','scripts.validate_publish'])

def publish_material():
    for attempt in range(1,4):
        run([sys.executable,'-m','scripts.material_change_manager','stage','--profile','local_agent'])
        staged=run(['git','diff','--cached','--name-only'],check=False).stdout.strip().splitlines()
        if not staged:
            print('Local agent: no material changes to publish.')
            clean_generated()
            return False
        run(['git','config','user.name','crm-local-agent'])
        run(['git','config','user.email','crm-local-agent@users.noreply.github.com'])
        run(['git','commit','-m','Refresh CRM local capital intelligence'])
        p=run(['git','push','origin','main'],check=False)
        if p.returncode==0:
            clean_generated()
            return True
        print(f'Local Agent: remote changed during publish; rebuilding generated state on latest main ({attempt}/3).')
        run(['git','fetch','origin','main'])
        subjects=_ahead_commit_subjects()
        non_runtime=[x for x in subjects if not x.startswith('Refresh CRM local capital intelligence')]
        if non_runtime:
            raise RuntimeError('Cannot safely rebuild: unpublished non-runtime commit detected.')
        run(['git','reset','--hard','origin/main'])
        _rebuild_intelligence()
        time.sleep(attempt*3)
    raise RuntimeError('Local agent could not publish after three rebuild-and-retry attempts.')

def run_module_with_heartbeat(mod,started,check=True):
    """Run a potentially long module while keeping the Local Agent heartbeat fresh."""
    proc=subprocess.Popen([sys.executable,'-m',mod],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    last=time.monotonic()
    while proc.poll() is None:
        if time.monotonic()-last>=20:
            write_status('RUNNING',f'Refreshing {mod}.',started,{'phase':mod,'heartbeat_at':now(),'process_running':True})
            last=time.monotonic()
        time.sleep(2)
    out,err=proc.communicate()
    if out:print(out,end='')
    if err:print(err,end='',file=sys.stderr)
    if check and proc.returncode:
        raise RuntimeError(f'Command failed: {sys.executable} -m {mod}')
    return proc.returncode

def _single_instance():
    lock=Path(os.getenv('TEMP') or '/tmp')/'crm_local_agent.lock'
    fh=open(lock,'a+')
    try:
        if os.name=='nt':
            import msvcrt; msvcrt.locking(fh.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl; fcntl.flock(fh,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return fh
    except OSError:
        fh.close(); return None
def main():
    guard=_single_instance()
    if guard is None:
        print('Local Agent already running; duplicate cycle skipped.')
        return 0
    os.environ['CRM_KUCOIN_HISTORY_SYNC']='1'
    ap=argparse.ArgumentParser(); ap.add_argument('--publish',action='store_true'); args=ap.parse_args(); started=now()
    write_status('RUNNING','Local Agent refresh started.',started,{'phase':'STARTING','heartbeat_at':now()})
    try:
        clean_generated()
        if not git_clean():
            write_status('BLOCKED','Local repository has source changes; automatic data refresh skipped.',started)
            return 2
        _safe_align_to_remote()
        for mod in MODULES:
            write_status('RUNNING',f'Refreshing {mod}.',started,{'phase':mod,'heartbeat_at':now()})
            run_module_with_heartbeat(mod,started)
            if mod=='scripts.kucoin_order_state':
                # Account → orders → fills have now run. Execute one same-cycle recovery transaction
                # before dependent portfolio/safety/freshness engines consume the state.
                write_status('RUNNING','Running KuCoin recovery transaction.',started,{'phase':'RECOVERY_TRANSACTION','heartbeat_at':now()})
                run_module_with_heartbeat('scripts.crm_health_recovery_engine',started,check=False)
        ku=json.loads((DOCS/'kucoin_account.json').read_text(encoding='utf-8-sig'))
        status='HEALTHY' if ku.get('status')=='ok' else 'DEGRADED'
        write_status(status,'Local private-data refresh completed.' if status=='HEALTHY' else 'Local agent ran but KuCoin remains degraded.',started,{'phase':'COMPLETE','completed_at':now(),'heartbeat_at':now(),'kucoin_status':ku.get('status'),'kucoin_diagnostic':(ku.get('diagnostic') or {}).get('category')})
        run([sys.executable,'-m','scripts.validate_publish'])
        if args.publish: publish_material()
        return 0 if status=='HEALTHY' else 1
    except Exception as exc:
        write_status('ERROR',str(exc)[:300],started)
        print('Local agent error:',exc)
        return 1
if __name__=='__main__': raise SystemExit(main())
