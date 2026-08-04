#!/usr/bin/env python3
"""V27 cloud scheduler entry point.
Runs the existing refresh/replay/discovery pipeline and always publishes a heartbeat.
It never changes live bots or production settings.
"""
from __future__ import annotations
import json, os, socket, traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from multi_coin_sync_backtest import main as pipeline_main
from core.candidate_validation import write_validation_queue
from core.decision_engine import write_decision_intelligence
from core.data_import import run_import_queue
from core.backtest_lab import run_lab

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / 'docs' / 'cloud_status.json'

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_status(state: str, started: str, error: str | None = None) -> None:
    strategies = {}
    discovery = {}
    for path, target in [(ROOT/'docs'/'strategies.json', strategies), (ROOT/'docs'/'coin_discovery.json', discovery)]:
        try: target.update(json.loads(path.read_text(encoding='utf-8-sig')))
        except Exception: pass
    payload = {
        'version': '29.0.0',
        'mode': 'cloud_autonomous_read_only',
        'state': state,
        'started_at': started,
        'completed_at': now(),
        'next_scheduled_at': (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat() if state == 'healthy' else None,
        'duration_seconds': max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(started)).total_seconds()) if started else None,
        'runner': os.getenv('GITHUB_ACTIONS') == 'true' and 'GitHub Actions' or socket.gethostname(),
        'workflow_run_id': os.getenv('GITHUB_RUN_ID'),
        'latest_strategy_snapshot': strategies.get('generated_at'),
        'latest_discovery_snapshot': discovery.get('generated_at'),
        'latest_replay_snapshot': strategies.get('generated_at'),
        'error': error,
        'safeguards': {
            'live_execution': False,
            'automatic_3commas_changes': False,
            'automatic_production_changes': False,
            'manual_approval_required': True,
        },
    }
    STATUS.write_text(json.dumps(payload, indent=2), encoding='utf-8')

if __name__ == '__main__':
    started = now()
    write_status('running', started)
    try:
        code = pipeline_main()
        if code != 0:
            raise RuntimeError(f'Pipeline returned status {code}')
        run_import_queue(ROOT)
        run_lab(ROOT)
        write_validation_queue(ROOT)
        write_decision_intelligence(ROOT)
        write_status('healthy', started)
        raise SystemExit(0)
    except Exception as exc:
        write_status('error', started, f'{type(exc).__name__}: {exc}')
        traceback.print_exc()
        raise SystemExit(1)
