#!/usr/bin/env python3
"""Read-only 3Commas DCA bot/deal synchroniser using RSA authentication.

Required GitHub Actions secrets:
- THREECOMMAS_API_KEY
- THREECOMMAS_RSA_PRIVATE_KEY_B64

The private key is decoded in memory only. It is never written to the repository,
workflow logs, or generated website data. Only BOTS_READ endpoints are called.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.json"
OUTPUT_PATH = ROOT / "docs" / "threecommas.json"
BASE_URL = "https://api.3commas.io"
from app.release import application_version
VERSION = application_version()
ALLOWED_PATHS = {"/public/api/ver1/validate", "/public/api/ver1/bots", "/public/api/ver1/deals", "/public/api/ver1/accounts"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_private_key(private_key_b64: str):
    try:
        pem = base64.b64decode(private_key_b64, validate=True)
    except Exception as exc:
        raise RuntimeError("THREECOMMAS_RSA_PRIVATE_KEY_B64 is not valid Base64.") from exc
    try:
        return serialization.load_pem_private_key(pem, password=None)
    except Exception as exc:
        raise RuntimeError("The decoded RSA private key is not a valid unencrypted PEM key.") from exc


def rsa_signature(payload: str, private_key) -> str:
    binary_signature = private_key.sign(
        payload.encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(binary_signature).decode("ascii")


def signed_get(path: str, params: dict[str, Any], api_key: str, private_key) -> Any:
    if path not in ALLOWED_PATHS:
        raise RuntimeError(f"Blocked non-approved 3Commas endpoint: {path}")
    query = urllib.parse.urlencode(params)
    full_path = path + ("?" + query if query else "")
    signature = rsa_signature(full_path, private_key)
    request = urllib.request.Request(
        BASE_URL + full_path,
        headers={
            "Apikey": api_key,
            "Signature": signature,
            "Accept": "application/json",
            "User-Agent": f"Crypto-Regime-Manager/{VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = body[:500]
        raise RuntimeError(f"3Commas HTTP {exc.code}: {detail}") from exc


def pair_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    return str(value or "")


def asset_from_pair(pair: Any) -> str | None:
    text = pair_text(pair).upper().replace("-", "_").replace("/", "_")
    tokens = [token for token in text.replace(",", "_").split("_") if token]
    quote = {"USDT", "USD", "USDC", "BTC", "XBT", "ETH", "EUR"}
    for token in reversed(tokens):
        if token not in quote and token:
            return "BTC" if token in {"XBT", "XXBT"} else token
    return None

def deal_status(deal: dict[str, Any]) -> str:
    for key in ("status", "status_string", "type"):
        if deal.get(key):
            return str(deal[key])
    return "Active"


def first_value(obj: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return None


def sanitise_bot(bot: dict[str, Any]) -> dict[str, Any]:
    base = to_float(first_value(bot, ("base_order_volume", "base_order_volume_value")))
    safety = to_float(first_value(bot, ("safety_order_volume", "safety_order_volume_value")))
    max_so = to_int(bot.get("max_safety_orders"))
    volume_scale = to_float(first_value(bot, ("martingale_volume_coefficient", "volume_scale")))
    theoretical = None
    if safety is not None and max_so is not None:
        scale = volume_scale or 1.0
        theoretical = sum(safety * (scale ** i) for i in range(max_so))
    return {
        "bot_id": to_int(bot.get("id")), "account_id": to_int(bot.get("account_id")),
        "name": str(bot.get("name") or "Unnamed bot"),
        "pair": pair_text(bot.get("pairs") or bot.get("pair")),
        "enabled": bool(bot.get("is_enabled", bot.get("enabled", False))),
        "active_deals": to_int(first_value(bot, ("active_deals_count", "active_deals"))) or 0,
        "max_active_deals": to_int(bot.get("max_active_deals")),
        "base_order_volume": base, "safety_order_volume": safety,
        "take_profit_pct": to_float(bot.get("take_profit")),
        "max_safety_orders": max_so,
        "max_active_safety_orders": to_int(first_value(bot, ("active_safety_orders_count", "max_active_safety_orders"))),
        "safety_order_deviation_pct": to_float(first_value(bot, ("safety_order_step_percentage", "price_deviation_to_open_safety_orders"))),
        "step_scale": to_float(first_value(bot, ("martingale_step_coefficient", "step_scale"))),
        "volume_scale": volume_scale,
        "start_condition": first_value(bot, ("strategy", "start_condition")),
        "start_order_type": first_value(bot, ("base_order_type", "start_order_type")),
        "safety_order_type": bot.get("safety_order_type"),
        "trailing_enabled": bool(first_value(bot, ("trailing_enabled", "trailing_deviation"))),
        "trailing_deviation": to_float(bot.get("trailing_deviation")),
        "cooldown_seconds": to_int(first_value(bot, ("cooldown", "cooldown_seconds"))),
        "reinvesting_percentage": to_float(first_value(bot, ("reinvesting_percentage", "reinvestment_percentage"))),
        "theoretical_max_dca_capital": (base or 0) + (theoretical or 0) if base is not None or theoretical is not None else None,
    }

def sanitise_deal(deal: dict[str, Any], publish_mode: str) -> dict[str, Any]:
    created = first_value(deal, ("created_at", "opened_at", "start_at"))
    result: dict[str, Any] = {
        "bot_name": str(deal.get("bot_name") or deal.get("name") or "3Commas DCA deal"),
        "pair": pair_text(deal.get("pair") or deal.get("pairs")),
        "status": deal_status(deal),
        "created_at": created,
        "profit_pct": to_float(first_value(deal, ("actual_profit_percentage", "profit_percentage"))),
        "completed_safety_orders": to_int(first_value(deal, ("completed_safety_orders_count", "completed_manual_safety_orders_count"))) or 0,
        "max_safety_orders": to_int(deal.get("max_safety_orders")),
        "active_safety_orders": to_int(first_value(deal, ("current_active_safety_orders_count", "active_safety_orders_count"))),
        "bot_id": to_int(deal.get("bot_id")),
        "capital_used": to_float(first_value(deal, ("bought_amount", "bought_volume", "base_order_volume"))),
        "placed_order_reserve": to_float(first_value(deal, ("reserved_quote_funds", "reserved_funds", "active_safety_order_capital"))),
    }
    if publish_mode == "full":
        result.update({
            "average_entry": to_float(first_value(deal, ("bought_average_price", "average_price", "base_order_average_price"))),
            "current_price": to_float(first_value(deal, ("current_price", "current_market_price", "last_price"))),
            "take_profit_price": to_float(first_value(deal, ("take_profit_price", "final_profit_price"))),
            "profit_usd": to_float(first_value(deal, ("actual_usd_profit", "usd_profit", "actual_profit"))),
            "bought_volume": to_float(first_value(deal, ("bought_volume", "base_order_volume"))),
            "capital_used": to_float(first_value(deal, ("bought_amount", "bought_volume", "reserved_base_coin"))),
        })
    return result



def sanitise_account(account: dict[str, Any]) -> dict[str, Any]:
    total = to_float(first_value(account, ("total_usd_value", "total_balance", "btc_amount")))
    free = to_float(first_value(account, ("available_usdt", "free_usdt", "available_balance", "balance")))
    return {
        "account_id": to_int(account.get("id")),
        "name": str(account.get("name") or account.get("exchange_name") or "3Commas account"),
        "exchange_name": first_value(account, ("exchange_name", "market_code", "type")),
        "currency": str(first_value(account, ("currency", "quote_currency")) or "USDT"),
        "total_usd_value": total,
        "free_usdt": free,
        "balance_source": "3Commas read-only account payload",
    }

def empty_payload(status: str, message: str, publish_mode: str = "masked") -> dict[str, Any]:
    return {
        "version": VERSION,
        "authentication": "RSA self-generated",
        "generated_at": now_iso(),
        "status": status,
        "message": message,
        "publish_mode": publish_mode,
        "read_only": True,
        "accounts": [],
        "assets": {},
    }


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    tcfg = config.get("threecommas", {})
    publish_mode = str(tcfg.get("publish_mode", "masked")).lower()
    if publish_mode not in {"masked", "full"}:
        publish_mode = "masked"

    api_key = os.getenv("THREECOMMAS_API_KEY", "").strip()
    private_key_b64 = os.getenv("THREECOMMAS_RSA_PRIVATE_KEY_B64", "").strip()
    if not api_key or not private_key_b64:
        payload = empty_payload(
            "not_configured",
            "Add THREECOMMAS_API_KEY and THREECOMMAS_RSA_PRIVATE_KEY_B64 as GitHub Actions secrets.",
            publish_mode,
        )
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0

    try:
        private_key = load_private_key(private_key_b64)
        # Authentication check first; this uses one Starter-plan read request.
        validation = signed_get("/public/api/ver1/validate", {}, api_key, private_key)
        if not isinstance(validation, dict) or validation.get("valid") is not True:
            raise RuntimeError(f"3Commas authentication validation failed: {validation}")

        bots_raw = signed_get("/public/api/ver1/bots", {"limit": 100, "offset": 0}, api_key, private_key)
        deals_raw = signed_get(
            "/public/api/ver1/deals",
            {"scope": "active", "limit": 1000, "offset": 0, "order_direction": "desc"},
            api_key,
            private_key,
        )
        if not isinstance(bots_raw, list):
            raise RuntimeError(f"Unexpected bots response type: {type(bots_raw).__name__}")
        if not isinstance(deals_raw, list):
            raise RuntimeError(f"Unexpected deals response type: {type(deals_raw).__name__}")

        accounts_raw = signed_get("/public/api/ver1/accounts", {}, api_key, private_key)
        if not isinstance(accounts_raw, list):
            raise RuntimeError(f"Unexpected accounts response type: {type(accounts_raw).__name__}")

        assets: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for bot in bots_raw:
            asset = asset_from_pair(bot.get("pairs") or bot.get("pair"))
            if asset:
                assets.setdefault(asset, {"bots": [], "deals": []})["bots"].append(sanitise_bot(bot))
        for deal in deals_raw:
            asset = asset_from_pair(deal.get("pair") or deal.get("pairs"))
            if asset:
                assets.setdefault(asset, {"bots": [], "deals": []})["deals"].append(sanitise_deal(deal, publish_mode))

        payload = {
            "version": VERSION,
            "authentication": "RSA self-generated",
            "generated_at": now_iso(),
            "status": "ok",
            "message": "Read-only 3Commas data updated successfully.",
            "publish_mode": publish_mode,
            "read_only": True,
            "accounts": [sanitise_account(a) for a in accounts_raw if isinstance(a, dict)],
            "assets": assets,
        }
    except Exception as exc:
        payload = empty_payload("error", str(exc), publish_mode)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"ok", "not_configured"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
