#!/usr/bin/env python3
"""Research-only KuCoin coin-discovery foundation for V23.

The scanner creates a reviewable universe and shortlist. It never changes
production strategies, 3Commas bots, or live execution settings.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from dataclasses import dataclass, asdict
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
    quote_volume_24h: float
    spread_pct: float | None
    listed_days: float | None
    eligible: bool
    reasons: list[str]
    stage: str = "discovered"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Crypto-Regime-Manager/23.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


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


def evaluate(symbol_row: dict[str, Any], ticker: dict[str, Any], cfg: dict[str, Any]) -> Candidate:
    rules = cfg["eligibility"]
    symbol = symbol_row.get("symbol", "")
    base = symbol_row.get("baseCurrency", "")
    quote = symbol_row.get("quoteCurrency", "")
    reasons: list[str] = []

    volume = float(ticker.get("volValue") or 0)
    buy = float(ticker.get("buy") or 0)
    sell = float(ticker.get("sell") or 0)
    mid = (buy + sell) / 2 if buy > 0 and sell > 0 else 0
    spread = ((sell - buy) / mid * 100) if mid > 0 else None

    if quote != cfg.get("quote_currency", "USDT"):
        reasons.append("wrong quote currency")
    if not symbol_row.get("enableTrading", False):
        reasons.append("trading disabled")
    if symbol in set(rules.get("exclude_symbols", [])):
        reasons.append("already configured")
    if rules.get("exclude_stablecoins", True) and base in STABLE_BASES:
        reasons.append("stablecoin excluded")
    if rules.get("exclude_leveraged_tokens", True) and base.endswith(LEVERAGED_SUFFIXES):
        reasons.append("leveraged token excluded")
    if volume < float(rules.get("minimum_24h_quote_volume_usdt", 0)):
        reasons.append("24h quote volume below minimum")
    if spread is None:
        reasons.append("spread unavailable")
    elif spread > float(rules.get("maximum_spread_pct", 999)):
        reasons.append("spread above maximum")

    return Candidate(
        symbol=symbol,
        base_currency=base,
        quote_currency=quote,
        quote_volume_24h=round(volume, 2),
        spread_pct=round(spread, 4) if spread is not None else None,
        listed_days=None,
        eligible=not reasons,
        reasons=reasons,
    )


def run(offline: bool = False) -> dict[str, Any]:
    app_cfg = load_json(CONFIG)
    cfg = app_cfg.get("coin_discovery", {})
    generated = datetime.now(timezone.utc).isoformat()

    if offline:
        registry_path = ROOT / cfg.get("universe_registry", "docs/coin_universe.json")
        prior = load_json(registry_path) if registry_path.exists() else {"candidates": []}
        candidates = prior.get("candidates", [])
        source = "existing registry (offline validation)"
    else:
        tickers = kucoin_tickers()
        candidates = [asdict(evaluate(row, tickers.get(row.get("symbol"), {}), cfg)) for row in kucoin_symbols()]
        source = "KuCoin public symbols and allTickers APIs"

    eligible = sorted(
        [c for c in candidates if c.get("eligible")],
        key=lambda c: float(c.get("quote_volume_24h") or 0),
        reverse=True,
    )
    limit = int((cfg.get("research_limits") or {}).get("maximum_shortlist", 20))
    shortlist = eligible[:limit]
    for rank, item in enumerate(shortlist, 1):
        item["rank"] = rank
        item["stage"] = "eligibility_passed"
        item["next_action"] = "Run full 4-hour history and DCA suitability research"

    result = {
        "version": "23.0.0",
        "generated_at": generated,
        "mode": "research_only",
        "source": source,
        "safeguards": {
            "automatic_add_to_production": False,
            "automatic_3commas_changes": False,
            "manual_approval_required": True,
        },
        "summary": {
            "symbols_reviewed": len(candidates),
            "eligible_symbols": len(eligible),
            "shortlist_size": len(shortlist),
        },
        "shortlist": shortlist,
        "candidates": candidates,
    }
    out = ROOT / cfg.get("output_json", "docs/coin_discovery.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    registry = ROOT / cfg.get("universe_registry", "docs/coin_universe.json")
    registry.write_text(json.dumps({"version": "23.0.0", "generated_at": generated, "candidates": candidates}, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Validate existing registry without network access")
    args = parser.parse_args()
    print(json.dumps(run(args.offline), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
