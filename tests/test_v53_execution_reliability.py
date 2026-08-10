from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_v(): assert (R/'VERSION').read_text(encoding='utf-8').strip()=='65.0.0'
def test_lock(): assert 'crm_local_agent.lock' in (R/'scripts/local_agent.py').read_text(encoding='utf-8')
def test_dashboard(): 
 h=(R/'docs/index.html').read_text(encoding='utf-8'); j=(R/'docs/unified_dashboard.js').read_text(encoding='utf-8')
 assert 'Portfolio Now' in h and 'Trading & Execution' in h and 'CRM Trading Plan — Test Mode' in j
def test_native_still_locked(): assert 'LIVE ORDER LOCK' in (R/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
