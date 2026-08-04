from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


def build_validation_queue(discovery: dict, *, max_candidates: int = 5) -> dict:
    candidates = []
    for item in (discovery.get('researched_candidates') or [])[:max_candidates]:
        proposal = item.get('advisory_dca') or {}
        candidates.append({
            'symbol': item.get('symbol'),
            'discovery_rank': item.get('rank'),
            'research_score': item.get('research_score'),
            'stage': 'queued_for_fee_aware_replay',
            'production_eligible': False,
            'manual_approval_required': True,
            'walk_forward_required': True,
            'proposed_dca': {
                'take_profit_pct': proposal.get('take_profit_pct'),
                'safety_order_deviation_pct': proposal.get('safety_order_deviation_pct'),
                'safety_orders': proposal.get('safety_orders'),
                'volume_scale': proposal.get('volume_scale'),
                'step_scale': proposal.get('step_scale'),
            },
            'gates': {
                'fee_aware_replay': 'pending',
                'independent_walk_forward': 'pending',
                'drawdown_review': 'pending',
                'capital_review': 'pending',
                'manual_approval': 'pending',
            },
            'next_action': 'Run full fee-aware replay before any forward test or production consideration.',
        })
    return {
        'version': '27.0.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'advisory_only_immutable_queue',
        'automatic_live_changes': False,
        'automatic_dca_changes': False,
        'candidate_count': len(candidates),
        'candidates': candidates,
    }


def write_validation_queue(root: Path) -> dict:
    source = root / 'docs' / 'coin_discovery.json'
    target = root / 'docs' / 'candidate_validation.json'
    discovery = json.loads(source.read_text(encoding='utf-8-sig')) if source.exists() else {}
    payload = build_validation_queue(discovery)
    target.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return payload
