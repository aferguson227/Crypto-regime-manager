from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v391_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='40.1.0'
 release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert release['release_name']=='Synchronisation & Workflow Efficiency'

def test_exactly_four_top_level_workflows():
 names=sorted(p.name for p in (ROOT/'.github/workflows').glob('*.yml'))
 assert names==['crm-data-refresh.yml','crm-health-self-heal.yml','crm-release-validation.yml','pages-deploy.yml']

def test_workflow_isolation_and_doctor():
 policy=json.loads((ROOT/'config/workflow_policy.json').read_text(encoding='utf-8'))
 groups=[x['concurrency_group'] for x in policy['workflows'].values()]
 assert len(groups)==len(set(groups))==4
 assert (ROOT/'scripts/workflow_doctor.py').exists()
 assert (ROOT/'scripts/github_workflow_telemetry.py').exists()

def test_actions_engine_reads_deploy_timeout_not_build_timeout():
 text=(ROOT/'scripts/github_actions_intelligence_engine.py').read_text(encoding='utf-8')
 assert 'def deploy_timeout' in text
 assert 'GITHUB_HOSTED_RUNNER_DELAY' in text
 assert "target_workflow_count':4" in text

def test_generated_cleanup_is_tracked_safe():
 text=(ROOT/'scripts/generated_output_manager.py').read_text(encoding='utf-8')
 assert 'def tracked(rel: str)' in text
 assert "'ls-files'" in text and "'--error-unmatch'" in text
 assert 'def restore_tracked(rel: str)' in text
 assert "'restore'" in text and "'--worktree'" in text

def test_data_refresh_is_quota_aware():
 w=(ROOT/'.github/workflows/crm-data-refresh.yml').read_text(encoding='utf-8')
 assert 'THREECOMMAS_BALANCE_REFRESH_MINUTES' in w
 assert 'hour % 4' in w
 integ=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding='utf-8')
 assert 'cached_quota_guard' in integ
 assert 'rate_limited_cached' in integ
