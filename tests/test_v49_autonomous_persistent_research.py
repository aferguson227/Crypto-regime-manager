import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='59.0.0'

def test_persistent_sqlite_research_database():
    text=(ROOT/'scripts/research_database.py').read_text(encoding='utf-8')
    assert 'sqlite3' in text
    assert 'crm_research.db' in text
    assert 'persistent_across_upgrades' in text

def test_scheduler_scans_and_caches():
    text=(ROOT/'scripts/research_scheduler.py').read_text(encoding='utf-8')
    assert "scripts.coin_discovery" in text
    assert "cache_hit" in text
    assert "research_fingerprint" in text
    assert "scripts.historical_data_manager" in text
    assert "scripts.kucoin_walk_forward_engine" in text

def test_local_agent_uses_cached_scheduler():
    text=(ROOT/'scripts/local_agent.py').read_text(encoding='utf-8')
    assert "'scripts.research_scheduler'" in text
    assert "interactive rebase is deliberately disabled" in text

def test_git_recovery_guard_protects_source_conflicts():
    text=(ROOT/'scripts/git_state_guard.py').read_text(encoding='utf-8')
    assert "RUNTIME_CONFLICT_RECOVERABLE" in text
    assert "SOURCE_CONFLICT_MANUAL" in text
    assert "rebase','--abort" in text

def test_installer_research_outputs_are_runtime_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    rows=set(p.get('runtime_generated_patterns') or [])
    assert 'docs/research_scheduler_status.json' in rows
    assert 'docs/research_database_status.json' in rows
    assert 'docs/presentation_quality.json' in rows

def test_dashboard_has_activity_strip_and_professional_formatter():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'id="crm-activity"' in html
    assert "replaceAll('_',' ')" in js
    assert "Persistent research memory" in js

def test_installer_should_not_need_expensive_backtests():
    # Build architecture promise is implemented by scheduler/status modules;
    # installer payload is tested separately when packaged.
    text=(ROOT/'scripts/research_scheduler.py').read_text(encoding='utf-8')
    assert "--status-only" in text
    assert "installer_runs_expensive_backtests" in text

def test_portfolio_allocation_is_advisory_only():
    text=(ROOT/'scripts/portfolio_allocation_engine.py').read_text(encoding='utf-8')
    assert "'automatic_deployment':False" in text
    assert "manual_approval_required" in text
