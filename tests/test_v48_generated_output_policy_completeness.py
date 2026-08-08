import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_cloud_and_health_runtime_outputs_are_classified():
    policy=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    runtime=set(policy.get('runtime_generated_patterns') or [])
    assert 'docs/cloud_status.json' in runtime
    assert 'docs/health_history.json' in runtime

def test_v48_policy_includes_all_new_local_agent_research_outputs():
    policy=json.loads((ROOT/'config/material_change_policy.json').read_text(encoding='utf-8'))
    paths=set(policy['profiles']['local_agent']['paths'])
    for rel in {
        'docs/historical_data_status.json',
        'docs/kucoin_walk_forward.json',
        'docs/research_activity.json',
        'docs/validation_resolution.json',
        'docs/independent_trade_accounting.json',
        'docs/source_health.json',
        'docs/market_universe_status.json',
    }:
        assert rel in paths
