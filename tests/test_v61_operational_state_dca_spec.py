import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='63.0.0'

def test_fast_local_agent_does_not_run_heavy_research_scheduler():
    import ast
    s=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    tree=ast.parse(s)
    mods=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(getattr(t,'id',None)=='MODULES' for t in node.targets):
            mods=ast.literal_eval(node.value)
    assert 'scripts.research_scheduler' not in mods
    assert "scripts.research_snapshot_bridge','import" in s

def test_research_worker_is_isolated():
    s=(ROOT/'scripts/research_worker.py').read_text(encoding='utf-8')
    assert 'shutil.copytree' in s
    assert "'scripts.research_scheduler'" in s
    assert "'scripts.research_snapshot_bridge','export'" in s

def test_windows_tasks_are_split():
    s=(ROOT/'UPDATE_LOCAL_AGENT_SCHEDULE.ps1').read_text(encoding='utf-8')
    assert 'CryptoRegimeManager-LocalAgent' in s
    assert 'CryptoRegimeManager-ResearchWorker' in s
    assert 'New-TimeSpan -Minutes 15' in s
    assert 'New-TimeSpan -Hours 6' in s

def test_freshness_uses_heartbeat():
    s=(ROOT/'scripts/freshness_controller.py').read_text(encoding='utf-8')
    assert "agent.get('heartbeat_at') or agent.get('completed_at')" in s
    assert 'Heavy research runs independently.' in s

def test_kucoin_last_good_truth_is_persistent():
    s=(ROOT/'scripts/integrations/kucoin_account.py').read_text(encoding='utf-8')
    assert 'kucoin_account_last_good.json' in s
    assert "'fallback_current'" in s
    assert 'save_last_good(payload)' in s

def test_private_recovery_requires_credentials():
    s=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    assert "private_ready=all(os.getenv(x,'').strip()" in s
    assert "'FALLBACK_CURRENT'" in s

def test_dca_spec_is_complete_and_truthful():
    s=(ROOT/'scripts/dca_deployment_spec_engine.py').read_text(encoding='utf-8')
    for k in ['base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders',
              'volume_scale','step_scale','max_active_safety_orders','max_active_deals','start_condition',
              'order_type','trailing_enabled','cooldown_seconds']:
        assert k in s
    assert 'FROZEN_BACKTEST_SETTING' in s
    assert 'GOVERNED_EXECUTION_DEFAULT' in s
    assert 'does not falsely label those sizes as optimised' in s

def test_deployment_queue_separates_required_and_safe_capital():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "stat('Capital required'" in js
    assert "stat('Safe allocation now'" in js
    assert 'No safe portfolio allocation is currently available' in js

def test_new_runtime_output_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    assert 'docs/dca_deployment_specs.json' in p.get('runtime_generated_patterns',[])

def test_live_execution_remains_locked():
    assert 'LIVE ORDER LOCK' in (ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
