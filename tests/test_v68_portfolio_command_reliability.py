from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')
def test_v68_version():
 assert text('VERSION').strip()=='68.0.0'
def test_briefing_no_longer_duplicates_live_and_next_cards():
 s=text('docs/unified_dashboard.js')
 assert '<span class="crm-command-label">Live position</span>' not in s
 assert '<span class="crm-command-label">Next opportunity</span>' not in s
def test_my_bots_is_operational_centre():
 s=text('docs/unified_dashboard.js')
 for x in ['Next capital priority','Regime','CRM decision','Continue paper trading']:
  assert x in s
def test_managed_bots_leave_deployment_queue():
 s=text('docs/unified_dashboard.js')
 assert "lifecycleReady.filter(x=>!managedSelected.has" in s
def test_paper_evidence_has_forward_metrics():
 s=text('scripts/paper_trading_engine.py')
 for x in ["'win_rate_pct'","'paper_days'","'profit_per_day_quote'","'max_drawdown_quote'"]:
  assert x in s
def test_health_is_evidence_driven():
 s=text('scripts/crm_health_recovery_engine.py')
 assert 'current_decision_truth' in s
 assert "'decision_data_usable':usable" in s
 assert "'severity':'low' if usable else 'high'" in s
def test_direct_execution_remains_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
