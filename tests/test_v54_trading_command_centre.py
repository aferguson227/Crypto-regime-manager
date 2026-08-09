import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version_is_v54():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='57.0.0'

def test_command_centre_is_first_class_dashboard_content():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert '<h2>Today’s Trading Briefing</h2>' in html
    assert 'id="trading-briefing"' in html
    assert '<h2>Ready for Deployment Review</h2>' in html
    assert 'id="deployment-ready-top"' in html
    for label in ['Portfolio value','Available for a new bot','Live trades','Realised P/L','Next bot for capital','Suggested next allocation']:
        assert label in js

def test_duplicate_primary_navigation_is_removed():
    text=(ROOT/'docs/design-system.js').read_text(encoding='utf-8')
    assert "const pages=[['Dashboard','index.html'],['Advanced','health.html']]" in text

def test_user_friendly_execution_language():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    for phrase in ['Trading & Execution','KuCoin connection','Trade protection','3Commas monitoring','CRM direct trading','Test trading plans']:
        assert phrase in html+js
    assert "stat('KuCoin order truth'" not in js

def test_realised_profit_uses_reconciled_fallback_chain():
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'liveTruth.realised_profit_quote??accounting.realised_profit_quote' in js
    assert 'Updating from KuCoin history' in js

def test_freshness_age_alone_is_not_source_overdue():
    text=(ROOT/'scripts/freshness_controller.py').read_text(encoding='utf-8')
    assert "overall='UPDATE_PENDING'" in text
    assert "overall='ACTION_REQUIRED'" in text
    assert "Website publishing is separate from trading-data reliability" in text
    assert "Age alone is informational" in text

def test_migration_progress_is_visible_and_read_only():
    text=(ROOT/'scripts/execution_migration_status_engine.py').read_text(encoding='utf-8')
    assert "'live_order_submission_enabled':False" in text
    assert "GUARDED_LIVE" in text
    assert "SECONDARY_TRANSITION_PROVIDER" in text
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'Migration to CRM direct trading' in js

def test_native_execution_lock_survives_v54():
    text=(ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
    assert 'LIVE ORDER LOCK' in text

def test_execution_migration_output_classified_runtime():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    assert 'docs/execution_migration_status.json' in set(p.get('runtime_generated_patterns') or [])
