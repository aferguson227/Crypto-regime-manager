import json
from pathlib import Path
from scripts.core.candidate_validation import build_validation_queue

ROOT = Path(__file__).resolve().parents[1]

def test_candidate_queue_is_advisory_and_immutable():
    discovery = {'researched_candidates':[{'symbol':'XMR-USDT','rank':1,'research_score':79.6,'advisory_dca':{'take_profit_pct':0.8,'safety_order_deviation_pct':0.8,'safety_orders':6,'volume_scale':1.5,'step_scale':1.1}}]}
    payload = build_validation_queue(discovery)
    assert payload['automatic_live_changes'] is False
    assert payload['automatic_dca_changes'] is False
    assert payload['candidates'][0]['manual_approval_required'] is True
    assert payload['candidates'][0]['gates']['fee_aware_replay'] == 'pending'

def test_v27_pages_use_shared_dark_shell_and_non_overlap_rules():
    cloud=(ROOT/'docs/cloud.html').read_text(encoding='utf-8')
    discovery=(ROOT/'docs/discovery.html').read_text(encoding='utf-8')
    css=(ROOT/'docs/v27.css').read_text(encoding='utf-8')
    assert 'v27-page v27-cloud-page' in cloud
    assert 'v27.css' in cloud and 'V63.0.0' in cloud
    assert 'data-v27-dense="true"' in discovery
    assert 'body[data-v27-dense="true"] .v25-cloud-badge' in css
    assert 'body.v27-cloud-page .v25-cloud-badge{display:none' in css

def test_release_metadata():
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    assert config['app']['version']=='63.0.0'
    assert (ROOT/'docs/validation_queue.html').exists()
