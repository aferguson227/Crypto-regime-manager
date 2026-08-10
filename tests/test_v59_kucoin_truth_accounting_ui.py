from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_version(): assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='59.0.0'
def test_order_collector_covers_provider_order_families():
 s=(ROOT/'scripts/kucoin_order_state.py').read_text(encoding='utf-8')
 assert "CLASSIC='/api/v1/orders'" in s and "STOP='/api/v1/stop-order'" in s and 'HF_ACTIVE' in s
 assert "'coverage':['HF orders','Classic orders','untriggered stop orders']" in s
def test_tp_absence_is_unverified_when_collection_degraded():
 s=(ROOT/'scripts/execution_assurance_engine.py').read_text(encoding='utf-8')
 assert "'UNVERIFIED' if not orders_healthy" in s
 assert "if not sells and orders_healthy" in s
 assert 'No leftover orders after a closed trade' in s
def test_unknown_open_pnl_is_not_zero():
 s=(ROOT/'scripts/live_portfolio_truth_engine.py').read_text(encoding='utf-8')
 assert "else (0.0 if not effective_open else None)" in s
 assert "'open_pnl_status'" in s
def test_cost_basis_backfill_is_bounded_and_persistent():
 s=(ROOT/'scripts/kucoin_fill_ledger.py').read_text(encoding='utf-8')
 assert "LEGACY_PATH='/api/v1/fills'" in s
 assert 'bounded_cost_basis_backfill' in s and 'max_windows=4' in s
 assert "key='backfill_cursor'" in s
def test_dashboard_uses_canonical_capital_first():
 s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
 assert 'capital.remaining_active_deal_dca_reserve??capital.reserved_capital' in s
 assert 'capital.deployable_capital??alloc.deployable_quote' in s
def test_badges_are_content_sized_and_no_hyphenation():
 s=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
 assert 'width:fit-content!important' in s and 'hyphens:none!important' in s
 assert 'align-self:flex-start!important' in s
def test_blank_cards_are_hidden():
 s=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
 assert "['market','sync','settings','operations','ui-quality','changes']" in s
 assert 'card.hidden=true' in s
def test_live_writes_still_locked():
 s=(ROOT/'scripts/native_execution_gateway.py').read_text(encoding='utf-8')
 assert 'LIVE ORDER LOCK' in s
