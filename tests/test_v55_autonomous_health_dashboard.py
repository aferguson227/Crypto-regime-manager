import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='57.0.0'

def test_health_recovery_engine_exists_and_has_hard_guardrails():
    text=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    assert 'CRM Health & Recovery' in text
    assert "'place/cancel KuCoin orders'" in text
    assert "'change API credentials'" in text
    assert "'Git push/force push'" in text
    assert "'scripts.kucoin_fill_ledger'" in text

def test_autonomous_diagnostics_applies_safe_repair_first():
    text=(ROOT/'scripts/autonomous_diagnostics.py').read_text(encoding='utf-8')
    assert "('scripts.self_healing_engine',('--apply-safe',))" in text
    assert "('scripts.crm_health_recovery_engine',('--repair',))" in text

def test_realised_pnl_has_progress_and_retry_metadata():
    text=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert "'reconciliation_progress_pct':progress" in text
    assert "'next_automatic_retry_minutes'" in text
    assert "'progress_explanation'" in text

def test_dashboard_has_system_health_and_runtime_layout_check():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert '<h2>System Health & Recovery</h2>' in html
    assert 'id="crm-health-recovery"' in html
    assert 'runtime-layout-check' in html
    assert 'Layout self-check' in js
    assert 'crm-overflow-safe' in js

def test_command_centre_metrics_stack_responsively():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert '.crm-command-grid>.crm-stat' in css
    assert 'grid-template-columns:1fr' in css
    assert '@media(max-width:640px)' in css

def test_coin_registry_is_card_based_not_squeezed_table():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'crm-coin-grid' in js
    assert 'crm-coin-card' in js
    assert '<th>Coin</th><th>Lifecycle</th>' not in js

def test_user_friendly_trading_safety_wording():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "stat('Trading safety checks'" in js
    assert "stat('Trade protection'" not in js

def test_health_output_is_runtime_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    assert 'docs/crm_health_recovery.json' in set(p.get('runtime_generated_patterns') or [])

def test_native_live_execution_remains_locked():
    text=(ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
    assert 'LIVE ORDER LOCK' in text
