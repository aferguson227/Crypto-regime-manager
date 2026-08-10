import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='67.0.0'

def test_private_symbol_scope_excludes_research_registry():
    s=(ROOT/'scripts/kucoin_symbol_scope.py').read_text(encoding='utf-8')
    assert "load('coin_registry.json')" not in s
    assert "load('candidate_review.json')" not in s
    assert "kucoin_fills.db" in s
    assert "add('TEL')" in s

def test_recovery_is_transactional_and_root_cause_based():
    s=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    for mod in ['scripts.kucoin_account_sync','scripts.kucoin_order_state','scripts.kucoin_fill_ledger',
                'scripts.execution_reconciliation_engine','scripts.independent_trade_accounting_engine',
                'scripts.execution_assurance_engine','scripts.freshness_controller']:
        assert mod in s
    assert 'Dependent freshness, P/L and safety symptoms are suppressed' in s
    assert 'consecutive_failed_cycles' in s
    assert 'recovery_actions_attempted' in s

def test_local_agent_keeps_heartbeat_during_long_modules():
    s=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert 'run_module_with_heartbeat' in s
    assert "'process_running':True" in s
    assert "'RECOVERY_TRANSACTION'" in s

def test_deployment_lifecycle_states():
    s=(ROOT/'scripts/deployment_lifecycle_engine.py').read_text(encoding='utf-8')
    for state in ['RESEARCHING','VALIDATING','READY_FOR_DEPLOYMENT_REVIEW','READY_TO_DEPLOY','RECOMMENDED_NOW','ACTIVE']:
        assert state in s
    assert "'automatic_live_deployment':False" in s
    assert 'Fixing Kraken continuation removes a blocker' in s

def test_ready_to_deploy_requires_complete_setup():
    s=(ROOT/'scripts/deployment_lifecycle_engine.py').read_text(encoding='utf-8')
    assert 'pct==100' in s
    assert 'continuation_resolved' in s
    assert "suggested_allocation_usdt" in s

def test_tel_profile_extracts_fuller_setup():
    s=(ROOT/'scripts/live_bot_profiles_engine.py').read_text(encoding='utf-8')
    assert "safety_order_deviation_pct" in s
    assert "max_active_safety_orders" in s
    assert "start_order_type" in s

def test_dashboard_has_direct_settings_and_deployment_plan():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert '<h2>Deployment Queue</h2>' in html
    assert 'id="bot-setup-modal"' in html
    assert 'View bot settings' in js
    assert 'View deployment plan' in js
    assert 'Exact DCA setup' in js

def test_health_ui_is_truthful():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'Recovery actions run' in js
    assert 'No recovery action was executed in this cycle.' in js
    assert 'CRM is retrying this automatically' not in js

def test_runtime_outputs_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    rows=set(p.get('runtime_generated_patterns') or [])
    assert 'docs/deployment_lifecycle.json' in rows
    assert 'docs/crm_health_recovery.json' in rows

def test_live_execution_still_locked():
    assert 'LIVE ORDER LOCK' in (ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
