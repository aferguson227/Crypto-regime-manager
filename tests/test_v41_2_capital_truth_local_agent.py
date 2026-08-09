from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def text(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_version(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='55.0.0'
def test_so_deviation_alias_is_canonical(): assert 'safety_order_deviation_pct' in text('scripts/deployment_intelligence_engine.py')
def test_bot_states_distinguish_active_and_idle():
    s=text('scripts/operating_state_engine.py'); assert 'ACTIVE_DEAL' in s and 'ENABLED_IDLE' in s and 'DISABLED' in s
def test_idle_bot_exposure_not_subtracted_from_deployable():
    s=text('scripts/capital_intelligence_engine.py'); assert "free-(remaining_total or 0.0)" in s and 'idle_bot_potential_exposure' in s
def test_portfolio_reserved_excludes_idle_potential():
    s=text('scripts/portfolio_intelligence_engine.py'); assert "reserved=num(cap.get('remaining_active_deal_dca_reserve'))" in s and 'idle_bot_potential_exposure' in s
def test_cloud_refresh_does_not_call_private_kucoin():
    s=text('.github/workflows/crm-data-refresh.yml'); assert 'python -m scripts.kucoin_account_sync' not in s and 'CRM_CAPITAL_PROVIDER: "LOCAL_KUCOIN"' in s
def test_local_agent_exists_and_remains_read_only():
    s=text('scripts/local_agent.py'); assert 'scripts.kucoin_account_sync' in s and 'execution_enabled' in s and "'write_trading_enabled':False" in s
def test_local_credentials_are_outside_repo(): assert 'LOCALAPPDATA' in text('SETUP_LOCAL_AGENT.ps1') and 'ConvertFrom-SecureString' in text('SETUP_LOCAL_AGENT.ps1')
def test_material_profile_includes_local_agent():
    d=json.loads(text('config/material_change_policy.json')); assert 'local_agent' in d['profiles']

def test_research_bridge_uses_kraken_registry_without_auto_promotion():
    s=text('scripts/research_evidence_engine.py'); assert 'walk_forward_registry.json' in s and "'automatic_production_promotion':False" in s
