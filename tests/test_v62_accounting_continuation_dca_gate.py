import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='69.0.0'

def test_targeted_deep_cost_basis_search():
    s=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert 'def targeted_deep_cost_basis_backfill' in s
    assert 'max_days=730' in s
    assert 'max_windows=12' in s
    assert "deep_backfill_cursor_" in s
    assert "'DEEP_COST_BASIS_SEARCH'" in s
    assert "'HISTORICAL_COST_BASIS_UNAVAILABLE'" in s

def test_kraken_q1_evidence_is_materialised_from_persistent_sources():
    s=(ROOT/'scripts/kraken_validation_evidence_manager.py').read_text(encoding='utf-8')
    assert r'C:\Crypto\Kraken Data\Q1_2026.zip' in s
    assert 'CRM_KRAKEN_VALIDATION_DIR' in s
    assert "data_root()/'Kraken'/'validation_4h'" in s
    assert 'import_file' in s
    assert 'never rewrite the original Kraken result' in s

def test_continuation_has_explicit_coverage_states():
    s=(ROOT/'scripts/cross_exchange_continuation_engine.py').read_text(encoding='utf-8')
    for state in ['KRAKEN_EVIDENCE_MATERIALISING','KUCOIN_HISTORY_ACQUIRING',
                  'KUCOIN_HISTORY_DOES_NOT_REACH_CUTOFF','KUCOIN_CONTINUATION_GAP',
                  'CLOSED_ON_KUCOIN_CONTINUATION']:
        assert state in s
    assert "'kucoin_coverage'" in s
    assert "'gap_hours'" in s

def test_research_worker_materialises_evidence_before_continuation():
    s=(ROOT/'scripts/research_scheduler.py').read_text(encoding='utf-8')
    assert "run('scripts.kraken_validation_evidence_manager'" in s
    assert "run('scripts.cross_exchange_continuation_engine'" in s
    assert "Same-cycle continuation re-evaluation" in s

def test_dca_optimisation_v2_is_training_then_unseen_validation():
    s=(ROOT/'scripts/dca_optimisation_v2_engine.py').read_text(encoding='utf-8')
    assert 'base_order_volume' in s and 'safety_order_volume' in s
    assert "bo_grid=[50.0,100.0,150.0]" in s
    assert "so_grid=[50.0,100.0,150.0]" in s
    assert "'COMPLETE' if passed else 'UNSEEN_VALIDATION_FAILED'" in s
    assert 'OPTIMISED_AND_UNSEEN_VALIDATED' in s
    assert 'GOVERNED_POLICY_NOT_OPTIMISED' in s

def test_exact_dca_settings_are_withheld_until_optimisation_passes():
    s=(ROOT/'scripts/dca_deployment_spec_engine.py').read_text(encoding='utf-8')
    assert "'recommended_dca_settings':strategy if strategy_complete else None" in s
    assert "'recommended_settings_available':strategy_complete" in s
    assert 'deliberately withholds exact deployment settings' in s

def test_candidate_readiness_includes_dca_and_continuation_gates():
    s=(ROOT/'scripts/candidate_review_engine.py').read_text(encoding='utf-8')
    assert "'dca_optimisation'" in s
    assert "'continuation_resolution'" in s
    assert 'continuation_gate_pass' in s

def test_deployment_lifecycle_blocks_unoptimised_or_unresolved_candidates():
    s=(ROOT/'scripts/deployment_lifecycle_engine.py').read_text(encoding='utf-8')
    assert "'DCA_OPTIMISATION_IN_PROGRESS'" in s
    assert 'optimisation_complete' in s
    assert 'continuation_resolved' in s
    assert 'capital_ready' in s
    assert 'CONTINUE_OPTIMISATION' in s

def test_system_health_excludes_accounting_limitations_from_root_issues():
    s=(ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
    assert "'informational_limitations':limitations" in s
    assert "'system_fault':False" in s
    assert 'PNL_RECONCILIATION' not in s

def test_dashboard_shows_optimisation_progress_not_fake_settings():
    s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert 'DCA setting optimisation in progress' in s
    assert 'Exact recommended settings are intentionally withheld' in s
    assert 'Deep history' in s
    assert 'Operational notes — not system faults' in s

def test_new_outputs_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    rows=set(p.get('runtime_generated_patterns') or [])
    assert 'docs/dca_optimisation_v2.json' in rows
    assert 'docs/kraken_validation_evidence_status.json' in rows

def test_native_execution_still_locked():
    assert 'LIVE ORDER LOCK' in (ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
