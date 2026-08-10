import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_version():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='62.0.0'

def test_execution_assurance_checks_tp_so_and_orphans():
    text=(ROOT/'scripts/execution_assurance_engine.py').read_text(encoding='utf-8')
    for marker in ['MISSING_TAKE_PROFIT_PROTECTION','SAFETY_ORDER_LADDER_INCOMPLETE','ORPHAN_ORDERS_WITHOUT_OPEN_POSITION','OPEN_POSITION_WITH_NO_MANAGEMENT_ORDERS']:
        assert marker in text
    assert "'automatic_exchange_writes':False" in text

def test_native_gateway_is_hard_locked():
    from scripts.native_execution_gateway import IntendedOrder,deterministic_client_oid,build_payload,submit_live_order,cancel_live_order
    oid=deterministic_client_oid('TEL','deal-1','BASE',0)
    assert oid.startswith('crm52-tel-')
    p=build_payload(IntendedOrder('TEL-USDT','buy','limit',size='100',price='0.0015'),oid)
    assert p['clientOid']==oid and p['symbol']=='TEL-USDT'
    with pytest.raises(RuntimeError):submit_live_order()
    with pytest.raises(RuntimeError):cancel_live_order()

def test_native_readiness_records_spot_contract_without_enabling_writes():
    text=(ROOT/'scripts/native_execution_readiness_engine.py').read_text(encoding='utf-8')
    assert "LOCKED_SHADOW" in text
    assert "'live_order_submission_implemented':False" in text
    policy=json.loads((ROOT/'config/v52_execution_assurance_policy.json').read_text(encoding='utf-8'))
    cfg=policy['native_execution']
    assert cfg['direct_order_endpoint']=='/api/v1/hf/orders'
    assert cfg['sync_order_endpoint']=='/api/v1/hf/orders/sync'
    assert cfg['required_permission']=='Spot'
    assert cfg['automatic_live_orders'] is False

def test_evidence_grades_block_short_history_deployment():
    text=(ROOT/'scripts/candidate_evidence_grade_engine.py').read_text(encoding='utf-8')
    assert "SCREEN_ONLY" in text
    assert "PRELIMINARY" in text
    assert "DEPLOYMENT_RESEARCH" in text
    assert "HIGH_CONFIDENCE" in text
    assert "deployment_history_gate" in text

def test_candidate_review_uses_evidence_grade_gate():
    text=(ROOT/'scripts/candidate_review_engine.py').read_text(encoding='utf-8')
    assert "'id':'evidence_grade'" in text
    assert "candidate_evidence_grades.json" in text

def test_unresolved_kraken_assets_are_prioritised_for_kucoin_history():
    h=(ROOT/'scripts/historical_data_manager.py').read_text(encoding='utf-8')
    q=(ROOT/'scripts/continuation_acquisition_queue_engine.py').read_text(encoding='utf-8')
    assert "continuation_acquisition_queue.json" in h
    assert "WAITING_FOR_COMPARABLE_DATA" in q
    assert "priority':'HIGH" in q

def test_freshness_only_critical_sources_can_make_source_overdue():
    text=(ROOT/'scripts/freshness_controller.py').read_text(encoding='utf-8')
    assert "DECISION_CRITICAL" in text
    assert "SECONDARY_PROVIDER" in text
    assert "PARTIALLY_DEGRADED" in text
    assert "Only decision-critical KuCoin/local-agent failures can produce Source overdue" in text

def test_dashboard_has_execution_control_and_evidence_grade():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    js=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "<h2>Execution Control</h2>" in html
    assert "executionAssurance" in js
    assert "nativeReadiness" in js
    assert "Evidence grade" in js
    assert "KUCOIN CURRENT · PROVIDER DEGRADED" in js

def test_new_runtime_outputs_are_classified():
    p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    rows=set(p.get('runtime_generated_patterns') or [])
    for rel in ['docs/execution_assurance.json','docs/native_execution_readiness.json','docs/candidate_evidence_grades.json','docs/continuation_acquisition_queue.json']:
        assert rel in rows
