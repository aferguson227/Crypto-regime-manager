import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v43_version(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='47.0.0'
def test_trade_engine_is_read_only():
    t=(ROOT/'scripts/trade_intelligence_engine.py').read_text(encoding='utf-8')
    assert "'bot_mutations':False" in t and "'order_mutations':False" in t and "'deal_closure':False" in t
    assert "'real_time_streaming':False" in t
def test_expansion_requires_manual_review():
    t=(ROOT/'scripts/expansion_readiness_engine.py').read_text(encoding='utf-8')
    assert "'one_new_asset_at_a_time':True" in t
    assert "'manual_approval_required':True" in t
    assert "'automatic_deployment':False" in t
def test_generated_output_policy_includes_v43_runtime_files():
    d=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    for x in ['docs/recommendation_history.json','docs/research_pipeline.json','docs/trade_intelligence.json','docs/expansion_readiness.json']:
        assert x in d['runtime_generated_patterns']
def test_dashboard_has_trade_and_expansion_cards():
    h=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert 'id="trade-intelligence"' in h and 'id="expansion-readiness"' in h
