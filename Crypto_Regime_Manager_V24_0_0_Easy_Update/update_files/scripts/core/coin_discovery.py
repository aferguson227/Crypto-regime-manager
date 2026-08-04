#!/usr/bin/env python3
"""V24 research-only KuCoin discovery and advisory DCA research.

This module scans the KuCoin USDT universe, applies liquidity/spread filters,
performs a bounded 4-hour market study on the strongest liquid candidates and
publishes reviewable DCA proposals. It never changes production settings,
3Commas bots or live execution state.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config.json"
STABLE_BASES = {"USDT", "USDC", "DAI", "TUSD", "FDUSD", "USDP", "EUR", "GBP"}
LEVERAGED_SUFFIXES = ("3L", "3S", "UP", "DOWN", "BULL", "BEAR")


@dataclass
class Candidate:
    symbol: str
    base_currency: str
    quote_currency: str
    last: float
    quote_volume_24h: float
    spread_pct: float | None
    change_24h_pct: float | None
    eligible: bool
    reasons: list[str]
    stage: str = "discovered"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fetch_json(url: str, retries: int = 3) -> dict[str, Any]:
    err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Crypto-Regime-Manager/24.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network dependent
            err = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Unable to fetch KuCoin data: {err}")


def kucoin_symbols() -> list[dict[str, Any]]:
    payload = fetch_json("https://api.kucoin.com/api/v2/symbols")
    if payload.get("code") != "200000":
        raise RuntimeError("Unexpected KuCoin symbols response")
    return payload.get("data") or []


def kucoin_tickers() -> dict[str, dict[str, Any]]:
    payload = fetch_json("https://api.kucoin.com/api/v1/market/allTickers")
    if payload.get("code") != "200000":
        raise RuntimeError("Unexpected KuCoin ticker response")
    return {x.get("symbol"): x for x in (payload.get("data") or {}).get("ticker", [])}


def candles_4h(symbol: str, count: int = 540) -> list[dict[str, float]]:
    end = int(time.time())
    start = end - count * 4 * 3600
    params = urllib.parse.urlencode({"symbol": symbol, "type": "4hour", "startAt": start, "endAt": end})
    payload = fetch_json(f"https://api.kucoin.com/api/v1/market/candles?{params}")
    if payload.get("code") != "200000":
        raise RuntimeError(f"Unexpected candle response for {symbol}")
    rows = []
    for r in reversed(payload.get("data") or []):
        try:
            rows.append({"ts": float(r[0]), "open": float(r[1]), "close": float(r[2]), "high": float(r[3]), "low": float(r[4]), "volume": float(r[5])})
        except (TypeError, ValueError, IndexError):
            continue
    return rows


def evaluate(symbol_row: dict[str, Any], ticker: dict[str, Any], cfg: dict[str, Any]) -> Candidate:
    rules = cfg["eligibility"]
    symbol = symbol_row.get("symbol", "")
    base = symbol_row.get("baseCurrency", "")
    quote = symbol_row.get("quoteCurrency", "")
    reasons: list[str] = []
    volume = float(ticker.get("volValue") or 0)
    buy, sell, last = (float(ticker.get(k) or 0) for k in ("buy", "sell", "last"))
    mid = (buy + sell) / 2 if buy > 0 and sell > 0 else 0
    spread = ((sell - buy) / mid * 100) if mid > 0 else None
    change_rate = ticker.get("changeRate")
    change = float(change_rate) * 100 if change_rate not in (None, "") else None

    if quote != cfg.get("quote_currency", "USDT"): reasons.append("wrong quote currency")
    if not symbol_row.get("enableTrading", False): reasons.append("trading disabled")
    if symbol in set(rules.get("exclude_symbols", [])): reasons.append("already configured")
    if rules.get("exclude_stablecoins", True) and base in STABLE_BASES: reasons.append("stablecoin excluded")
    if rules.get("exclude_leveraged_tokens", True) and base.endswith(LEVERAGED_SUFFIXES): reasons.append("leveraged token excluded")
    if volume < float(rules.get("minimum_24h_quote_volume_usdt", 0)): reasons.append("24h quote volume below minimum")
    if last <= 0: reasons.append("last price unavailable")
    if spread is None: reasons.append("spread unavailable")
    elif spread > float(rules.get("maximum_spread_pct", 999)): reasons.append("spread above maximum")

    return Candidate(symbol, base, quote, last, round(volume, 2), round(spread, 4) if spread is not None else None,
                     round(change, 3) if change is not None else None, not reasons, reasons)


def pct_returns(closes: list[float]) -> list[float]:
    return [(b / a - 1) * 100 for a, b in zip(closes, closes[1:]) if a > 0]


def max_drawdown(closes: list[float]) -> float:
    peak = 0.0
    worst = 0.0
    for x in closes:
        peak = max(peak, x)
        if peak > 0:
            worst = min(worst, (x / peak - 1) * 100)
    return worst


def analyse_market(c: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    rows = candles_4h(c["symbol"], int((cfg.get("deep_research") or {}).get("history_candles", 540)))
    closes = [r["close"] for r in rows]
    rets = pct_returns(closes)
    if len(closes) < 120 or not rets:
        return {**c, "research_status": "insufficient_history", "history_candles": len(closes), "research_score": 0}

    vol_20d = statistics.pstdev(rets[-120:]) * math.sqrt(6 * 365) if len(rets) >= 120 else 0
    median_abs = statistics.median(abs(x) for x in rets[-120:])
    trend_30d = (closes[-1] / closes[-180] - 1) * 100 if len(closes) >= 180 else 0
    dd = max_drawdown(closes)
    liquidity_score = min(100.0, math.log10(max(float(c["quote_volume_24h"]), 1)) / 8 * 100)
    spread_score = max(0.0, 100 - float(c.get("spread_pct") or 99) / max(float(cfg["eligibility"].get("maximum_spread_pct", .6)), .01) * 100)
    volatility_score = max(0.0, 100 - abs(median_abs - 1.0) * 45)
    drawdown_score = max(0.0, 100 + dd * 1.8)
    trend_score = max(0.0, min(100.0, 50 + trend_30d * 1.5))
    score = round(.28*liquidity_score + .18*spread_score + .24*volatility_score + .18*drawdown_score + .12*trend_score, 1)

    # Conservative, bounded advisory DCA proposal derived from observed 4h movement.
    tp = min(3.0, max(0.8, round(median_abs * 1.25, 1)))
    so_dev = min(5.0, max(0.8, round(median_abs * 1.5, 1)))
    max_so = 6 if dd > -35 else 7
    volume_scale = 1.4 if dd > -25 else 1.5
    step_scale = 1.1 if vol_20d < 80 else 1.2
    capital_risk = "medium" if dd > -35 else "high"
    return {
        **c,
        "research_status": "screened",
        "history_candles": len(closes),
        "annualised_realised_vol_pct": round(vol_20d, 1),
        "median_4h_move_pct": round(median_abs, 3),
        "trend_30d_pct": round(trend_30d, 1),
        "historical_drawdown_pct": round(dd, 1),
        "research_score": score,
        "advisory_dca": {
            "take_profit_pct": tp,
            "safety_order_deviation_pct": so_dev,
            "safety_orders": max_so,
            "volume_scale": volume_scale,
            "step_scale": step_scale,
            "risk_band": capital_risk,
            "status": "proposal_only",
            "next_action": "Run full fee-aware replay and independent walk-forward validation"
        }
    }


def run(offline: bool = False) -> dict[str, Any]:
    app_cfg = load_json(CONFIG)
    cfg = app_cfg.get("coin_discovery", {})
    generated = datetime.now(timezone.utc).isoformat()
    registry_path = ROOT / cfg.get("universe_registry", "docs/coin_universe.json")

    if offline:
        prior = load_json(registry_path) if registry_path.exists() else {"candidates": []}
        candidates = prior.get("candidates", [])
        source = "existing registry (offline validation)"
    else:
        tickers = kucoin_tickers()
        candidates = [asdict(evaluate(row, tickers.get(row.get("symbol"), {}), cfg)) for row in kucoin_symbols()]
        source = "KuCoin public symbols, tickers and bounded 4-hour candle research"

    eligible = sorted([c for c in candidates if c.get("eligible")], key=lambda c: float(c.get("quote_volume_24h") or 0), reverse=True)
    shortlist_limit = int((cfg.get("research_limits") or {}).get("maximum_shortlist", 20))
    shortlist = eligible[:shortlist_limit]
    deep_limit = int((cfg.get("deep_research") or {}).get("maximum_assets_per_run", 5))
    researched: list[dict[str, Any]] = []
    if not offline:
        for item in shortlist[:deep_limit]:
            try:
                researched.append(analyse_market(dict(item), cfg))
            except Exception as exc:  # pragma: no cover - network dependent
                researched.append({**item, "research_status": "error", "research_error": str(exc), "research_score": 0})
            time.sleep(float((cfg.get("deep_research") or {}).get("request_pause_seconds", .25)))
    else:
        researched = (load_json(ROOT / cfg.get("output_json", "docs/coin_discovery.json")).get("researched_candidates", [])
                      if (ROOT / cfg.get("output_json", "docs/coin_discovery.json")).exists() else [])

    researched.sort(key=lambda x: float(x.get("research_score") or 0), reverse=True)
    for rank, item in enumerate(researched, 1):
        item["rank"] = rank
        item["stage"] = "dca_research_proposal" if item.get("research_status") == "screened" else "review_required"

    result = {
        "version": "24.0.0", "generated_at": generated, "mode": "research_only", "source": source,
        "safeguards": {"automatic_add_to_production": False, "automatic_3commas_changes": False,
                       "automatic_dca_changes": False, "manual_approval_required": True,
                       "full_replay_required": True, "forward_validation_required": True},
        "summary": {"symbols_reviewed": len(candidates), "eligible_symbols": len(eligible),
                    "shortlist_size": len(shortlist), "deep_research_completed": sum(x.get("research_status")=="screened" for x in researched),
                    "dca_proposals": sum(bool(x.get("advisory_dca")) for x in researched)},
        "researched_candidates": researched, "shortlist": shortlist, "candidates": candidates,
    }
    out = ROOT / cfg.get("output_json", "docs/coin_discovery.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    registry_path.write_text(json.dumps({"version":"24.0.0","generated_at":generated,"candidates":candidates}, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.offline), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
