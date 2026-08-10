from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_version(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='61.0.0'
def test_progress():
 s=(ROOT/'scripts/continuation_acquisition_queue_engine.py').read_text(encoding='utf-8')
 assert 'DOWNLOADING_CONTINUATION_HISTORY' in s and 'estimated_background_cycles_remaining' in s and 'estimated_minutes_remaining' in s
def test_schedule():
 s=(ROOT/'scripts/local_agent_schedule_health.py').read_text(encoding='utf-8')
 assert 'CryptoRegimeManager-LocalAgent' in s and "'last_run'" in s and "'next_run'" in s
def test_health_schedule():
 assert 'LOCAL_AGENT_SCHEDULE' in (ROOT/'scripts/crm_health_recovery_engine.py').read_text(encoding='utf-8')
def test_pnl_wording():
 s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8');assert 'Updating · Unknown' not in s and 'Reconciliation pending' in s
def test_hyphens():
 s=(ROOT/'docs/design-system.css').read_text(encoding='utf-8');assert 'hyphens:none' in s
def test_classified():
 p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8'));assert 'docs/local_agent_schedule_health.json' in p['runtime_generated_patterns']
def test_lock():
 assert 'LIVE ORDER LOCK' in (ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
