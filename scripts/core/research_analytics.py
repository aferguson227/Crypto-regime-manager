from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _regime(discovery: dict[str, Any] | None, training: dict[str, Any]) -> dict[str, Any]:
    discovery = discovery or {}
    trend = float(discovery.get("trend_30d_pct") or 0)
    vol = float(discovery.get("annualised_realised_vol_pct") or 0)
    avg_hours = float(training.get("average_hours") or 0)
    if abs(trend) >= 15:
        label = "TRENDING"
    elif vol >= 70:
        label = "HIGH VOLATILITY"
    elif avg_hours <= 24:
        label = "MEAN REVERTING"
    else:
        label = "MIXED"
    return {"label": label, "trend_30d_pct": trend, "annualised_vol_pct": vol}


def _families(regime: str) -> list[dict[str, Any]]:
    # Screening priorities only. Every family still requires its own fee-aware replay.
    if regime == "TRENDING":
        rows = [("Trend-filtered DCA", 90), ("Breakout / momentum", 78), ("Grid", 35), ("QFL", 42)]
    elif regime == "HIGH VOLATILITY":
        rows = [("QFL + DCA", 88), ("Wide-ladder DCA", 82), ("Dynamic grid", 65), ("Momentum", 45)]
    elif regime == "MEAN REVERTING":
        rows = [("Grid", 88), ("DCA", 84), ("QFL + DCA", 75), ("Momentum", 35)]
    else:
        rows = [("Regime-filtered DCA", 82), ("Dynamic grid", 70), ("QFL + DCA", 68), ("Momentum", 55)]
    return [{"family": n, "screening_score": s, "status": "REQUIRES INDEPENDENT BACKTEST"} for n, s in rows]


def _heatmap(settings: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    # A transparent local sensitivity grid around the frozen DCA settings. It is not a substitute for replay.
    tp = float(settings.get("take_profit_pct") or 1.0)
    dev = float(settings.get("so_deviation_pct") or 1.0)
    pnl = float(metrics.get("mark_to_market_pnl", metrics.get("net_pnl", 0)) or 0)
    capital = max(float(metrics.get("max_capital") or 1), 1)
    base = max(-100.0, min(100.0, 50 + 50 * pnl / capital))
    cells=[]
    for t in (max(.2,tp-.4), tp, tp+.4):
        for d in (max(.2,dev-.3), dev, dev+.3):
            distance=abs(t-tp)/max(tp,.1)+abs(d-dev)/max(dev,.1)
            cells.append({"take_profit_pct":round(t,2),"so_deviation_pct":round(d,2),"sensitivity_score":round(base-12*distance,1),"kind":"LOCAL SENSITIVITY — RUN REPLAY TO VERIFY"})
    return {"baseline":{"take_profit_pct":tp,"so_deviation_pct":dev},"cells":cells}


def write_research_analytics(root: Path) -> dict[str, Any]:
    docs=root/"docs"
    wf=_read(docs/"walk_forward_registry.json")
    discovery=_read(docs/"coin_discovery.json")
    dmap={str(x.get("base_currency") or str(x.get("symbol","")).split("-")[0]).upper():x for x in discovery.get("researched_candidates",[])}
    coins=[]
    for coin in wf.get("coins",[]):
        symbol=str(coin.get("symbol","")).upper()
        tr=coin.get("training_metrics") or {}
        va=coin.get("q1_2026_metrics") or {}
        train_per_deal=_safe_div(float(tr.get("net_pnl") or 0),float(tr.get("closed_deals") or 0))
        val_per_deal=_safe_div(float(va.get("mark_to_market_pnl",va.get("net_pnl",0)) or 0),float(va.get("closed_deals") or 0))
        degradation=100*(1-_safe_div(val_per_deal,train_per_deal)) if train_per_deal else 0
        regime=_regime(dmap.get(symbol),tr)
        coins.append({
            "symbol":symbol,"status":coin.get("status"),"next_stage":coin.get("next_stage"),
            "regime":regime,"strategy_family_screening":_families(regime["label"]),
            "walk_forward":{"training_pnl_per_deal":round(train_per_deal,2),"validation_mtm_pnl_per_deal":round(val_per_deal,2),"degradation_pct":round(degradation,1),"validation_deals":va.get("closed_deals",0),"validation_drawdown_pct":round(100*_safe_div(abs(float(va.get("max_drawdown_dollars") or 0)),float(va.get("max_capital") or 0)),1)},
            "dca_sensitivity":_heatmap(coin.get("frozen_settings") or {},va),
            "frozen_settings":coin.get("frozen_settings") or {},
            "production_eligible":False,
        })
    payload={"version":"31.1.0","generated_at":datetime.now(timezone.utc).isoformat(),"mode":"research_intelligence_read_only","coins":coins,"summary":{"coins":len(coins),"walk_forward_passes":sum(c.get("status")=="PASS" for c in coins),"requires_review":sum(abs(c["walk_forward"]["degradation_pct"])>50 for c in coins)},"safeguards":{"automatic_bot_creation":False,"automatic_strategy_changes":False,"manual_approval_required":True,"sensitivity_is_not_backtest":True}}
    (docs/"research_analytics.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    report={"version":"31.1.0","generated_at":payload["generated_at"],"title":"Crypto Regime Research Report","executive_summary":payload["summary"],"candidates":[{"symbol":c["symbol"],"status":c["status"],"regime":c["regime"]["label"],"preferred_family":c["strategy_family_screening"][0]["family"],"degradation_pct":c["walk_forward"]["degradation_pct"],"next_action":"Run independent fee-aware replay for the shortlisted strategy family; retain manual approval."} for c in coins],"disclaimer":"Research-only evidence. No live bot or 3Commas setting is changed automatically."}
    (docs/"research_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return payload
