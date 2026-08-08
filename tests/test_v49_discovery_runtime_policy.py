import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_coin_discovery_and_universe_are_runtime_outputs():
    policy = json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'))
    runtime = set(policy.get('runtime_generated_patterns') or [])
    assert 'docs/coin_discovery.json' in runtime
    assert 'docs/coin_universe.json' in runtime
