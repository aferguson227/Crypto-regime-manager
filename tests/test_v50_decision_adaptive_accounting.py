import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='62.0.0'

def test_fill_ledger_is_read_only_and_persistent():
    text=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
    assert "/api/v1/hf/fills" in text
    assert "Accounting'/'kucoin_fills.db" in text
    assert "'write_endpoints_implemented':False" in text
    assert "POST" not in text and "DELETE" not in text

def test_accounting_consumes_kucoin_fill_ledger():
    text=(ROOT/'scripts/independent_trade_accounting_engine.py').read_text(encoding='utf-8')
    assert "kucoin_fill_ledger.json" in text
    assert "KuCoin persistent fill ledger" in text

def test_candidate_review_has_five_explainable_gates():
    text=(ROOT/'scripts/candidate_review_engine.py').read_text(encoding='utf-8')
    for gate in ['history_complete','kucoin_walk_forward','trade_fluidity','current_regime_fit','capital_allocation']:
        assert gate in text
    assert "deployment_preparation_available" in text
    assert "automatic_deployment':False" in text

def test_adaptive_research_preserves_unseen_validation():
    text=(ROOT/'scripts/adaptive_candidate_research_engine.py').read_text(encoding='utf-8')
    assert "ADAPTIVE_RESEARCH_QUEUED" in text
    assert "must be selected on training data and re-tested on unseen KuCoin validation data" in text
    wf=(ROOT/'scripts/kucoin_walk_forward_engine.py').read_text(encoding='utf-8')
    assert "adaptive_research_applied" in wf
    assert "search_extensions" in wf

def test_research_db_reconciles_existing_assets():
    text=(ROOT/'scripts/research_database.py').read_text(encoding='utf-8')
    assert "record_assets();import_candidate_state()" in text

def test_semantic_publication_freshness():
    text=(ROOT/'scripts/freshness_controller.py').read_text(encoding='utf-8')
    assert "Live Pages is synchronised" in text
    assert "content_pending" in text

def test_cloud_watchdog_distinguishes_non_blocking_age():
    text=(ROOT/'scripts/cloud_reliability_engine.py').read_text(encoding='utf-8')
    assert "decision_blocking" in text
    assert "publication age alone is not a reliability fault" in text

def test_dashboard_has_review_candidate_and_prepare_deployment():
    text=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "Review candidate" in text
    assert "Prepare deployment" in text
    assert "crm_deployment_preparation_v1" in text
    assert "ageText" in text and "dateText" in text

def test_all_new_runtime_outputs_are_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    runtime=set(p.get('runtime_generated_patterns') or [])
    for rel in ['docs/kucoin_fill_ledger.json','docs/adaptive_research_queue.json','docs/candidate_review.json','docs/coin_discovery.json','docs/coin_universe.json']:
        assert rel in runtime
