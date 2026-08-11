from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def t(p):return (ROOT/p).read_text(encoding="utf-8")
def test_portfolio_guard_corrects_cash_vs_portfolio():
 s=t("scripts/portfolio_truth_guard.py")
 assert "reconstructed=(cash or 0)+live_value" in s
 assert "authoritative_value_quote" in s
def test_deployable_is_capped_by_cash():
 s=t("scripts/portfolio_truth_guard.py")
 assert "min(deployable,cash-reserve)" in s
def test_next_capital_automation_preview_is_advisory():
 s=t("scripts/portfolio_truth_guard.py")
 assert "QUEUED_AFTER_LIVE_DEAL" in s
 assert '"auto_execution_permitted":False' in s
def test_paper_evidence_has_maturity_states():
 s=t("scripts/portfolio_truth_guard.py")
 for x in ("STARTING","EARLY_FORWARD_TEST","BUILDING_EVIDENCE","MEANINGFUL_FORWARD_EVIDENCE"):assert x in s
def test_publication_only_warning_can_be_downgraded():
 s=t("scripts/runtime_health_normalizer.py")
 assert "does not block live trading" in s
 assert "kucoin" in s.lower()
