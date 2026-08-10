from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_version(): assert text('VERSION').strip()=='66.0.0'
def test_resident_service_is_read_only_and_frequent():
 s=text('scripts/kucoin_live_data_service.py')
 assert "'fast_interval_seconds':20" in s
 assert "'private_refresh_interval_seconds':60" in s
 assert "'write_endpoints_implemented':False" in s
 assert 'research' not in s.lower().split("fast=")[1].split("medium=")[0]
def test_resident_service_uses_same_local_credentials():
 s=text('RUN_KUCOIN_LIVE_SERVICE.ps1')
 for k in ['KUCOIN_API_KEY','KUCOIN_API_SECRET','KUCOIN_API_PASSPHRASE']: assert k in s
 assert 'kucoin_credentials.json' in s
def test_schedule_starts_live_service_at_logon():
 s=text('UPDATE_LOCAL_AGENT_SCHEDULE.ps1')
 assert 'CryptoRegimeManager-LiveDataService' in s
 assert r'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' in s
 assert "New-ItemProperty -Path $RunKey -Name $LiveName" in s
 assert "Start-Process -FilePath 'powershell.exe'" in s

def test_browser_updates_live_pnl_every_15_seconds():
 s=text('docs/unified_dashboard.js')
 assert 'refreshBrowserLivePnl' in s
 assert 'setInterval(refreshBrowserLivePnl,15000)' in s
 assert 'Live browser KuCoin price' in s
def test_pnl_percentages_are_exposed():
 s=text('scripts/live_portfolio_truth_engine.py')
 assert "'open_pnl_pct'" in s and "'open_capital_quote'" in s
 js=text('docs/unified_dashboard.js')
 assert 'realisedPnlPct' in js and 'totalPnlPct' in js
def test_dashboard_data_destructuring_matches_v2_outputs():
 s=text('docs/unified_dashboard.js')
 assert 'portfolioCapitalV2,integrityStatus,liveRevalidation,fastLiveTruth,canonicalKucoin,livePrices,liveService,ver' in s
def test_order_collector_has_all_open_hf_endpoint():
 s=text('scripts/kucoin_order_state.py')
 assert "HF_ACTIVE_ALL='/api/v1/hf/orders/active'" in s
 assert "'HF all-open orders'" in s
def test_deployment_modal_does_not_render_missing_cross_category_fields():
 s=text('docs/unified_dashboard.js')
 assert 'optimisedSetupKeys' in s and 'governedControlKeys' in s
 assert "present=order.filter" in s
def test_validation_failures_enter_fresh_research_queue():
 s=text('scripts/dca_reoptimisation_queue_engine.py')
 assert 'QUEUED_FOR_FRESH_RESEARCH' in s
 assert 'will not tune against the failed unseen result' in s
def test_multibot_manager_keeps_conditional_capacity_advisory():
 s=text('scripts/portfolio_capital_manager_v2.py')
 assert 'conditional_multi_bot_capacity_usdt' in s
 assert "'conditional_capacity_is_advisory_only':True" in s
 assert 'safe_multi_bot_pool_usdt' in s
def test_live_strategy_revalidation_is_no_midtrade_mutation():
 s=text('scripts/live_strategy_revalidation_engine.py')
 assert "'would_deploy_today'" in s
 assert "'automatic_mid_trade_setting_change':False" in s
def test_native_execution_still_locked():
 assert 'LIVE ORDER LOCK' in text('scripts/native_execution_gateway.py')
