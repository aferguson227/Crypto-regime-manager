from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_v46_identity(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='46.0.0'
def test_silent_agent_task():
 t=(ROOT/'UPDATE_LOCAL_AGENT_SCHEDULE.ps1').read_text(encoding='utf-8'); assert '-WindowStyle Hidden' in t and '-Minutes 15' in t
def test_v46_engines_present():
 for n in ['market_universe_engine.py','historical_data_manager.py','validation_resolution_engine.py','independent_trade_accounting_engine.py','source_health_engine.py']: assert (ROOT/'scripts'/n).exists()
def test_btc_is_research_only():
 c=json.loads((ROOT/'config.json').read_text(encoding='utf-8')); d=c['coin_discovery']; assert 'BTC' in d['experimental_quote_currencies'] and d['experimental_btc_pairs_research_only'] is True
def test_outputs_classified():
 p=json.loads((ROOT/'config/generated_outputs_policy.json').read_text(encoding='utf-8')); r=set(p['runtime_generated_patterns']); assert {'docs/market_universe_status.json','docs/historical_data_status.json','docs/validation_resolution.json','docs/independent_trade_accounting.json','docs/source_health.json'}<=r
def test_live_portfolio_dashboard():
 assert 'Live Portfolio' in (ROOT/'docs/index.html').read_text(encoding='utf-8') and 'independent_trade_accounting.json' in (ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
def test_manual_execution_guardrails():
 text=(ROOT/'scripts/independent_trade_accounting_engine.py').read_text(encoding='utf-8'); assert "'execution_enabled':False" in text and "'read_only':True" in text
