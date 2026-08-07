#!/usr/bin/env python3
"""Read-only 3Commas DCA bot/deal synchroniser using RSA authentication.

Required GitHub Actions secrets:
- THREECOMMAS_API_KEY
- THREECOMMAS_RSA_PRIVATE_KEY_B64

The private key is decoded in memory only. It is never written to the repository,
workflow logs, or generated website data. Only approved BOTS_READ and ACCOUNTS_READ endpoints are called. No trading or account mutations are permitted.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class ThreeCommasEndpointError(RuntimeError):
    def __init__(self, path: str, category: str, message: str, http_status: int | None = None):
        super().__init__(message); self.path=path; self.category=category; self.http_status=http_status


from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.json"
OUTPUT_PATH = ROOT / "docs" / "threecommas.json"
BASE_URL = "https://api.3commas.io"
from app.release import application_version
VERSION = application_version()
STATIC_ALLOWED_REQUESTS = {
    ("GET", "/public/api/ver1/validate"),
    ("GET", "/public/api/ver1/bots"),
    ("GET", "/public/api/ver1/deals"),
    ("GET", "/public/api/ver1/accounts"),
}
ALLOWED_PATHS = {path for method, path in STATIC_ALLOWED_REQUESTS if method == "GET"}
ACCOUNT_READ_PATH = re.compile(r"^/public/api/ver1/accounts/(\d+)$")
ACCOUNT_BALANCE_PATH = re.compile(r"^/public/api/ver1/accounts/(\d+)/account_table_data$")


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


def request_is_approved(method: str, path: str) -> bool:
    method = method.upper()
    if (method, path) in STATIC_ALLOWED_REQUESTS:
        return True
    if method == "GET" and ACCOUNT_READ_PATH.fullmatch(path):
        return True
    # account_table_data is a documented ACCOUNTS_READ operation. It uses HTTP
    # POST for a read-only table query but cannot place orders or change accounts.
    if method == "POST" and ACCOUNT_BALANCE_PATH.fullmatch(path):
        return True
    return False


def signed_request(method: str, path: str, params: dict[str, Any], api_key: str, private_key) -> Any:
    method = method.upper()
    if not request_is_approved(method, path):
        raise RuntimeError(f"Blocked non-approved 3Commas request: {method} {path}")
    encoded = urllib.parse.urlencode(params)
    query = encoded if method == "GET" else ""
    body = encoded.encode("ascii") if method == "POST" and encoded else (b"" if method == "POST" else None)
    full_path = path + ("?" + query if query else "")
    # 3Commas RSA signing covers the request path and query. Empty-body read POSTs
    # therefore sign the path exactly as documented.
    signature = rsa_signature(full_path, private_key)
    headers={
        "Apikey": api_key, "Signature": signature, "Accept": "application/json",
        "User-Agent": f"Crypto-Regime-Manager/{VERSION}",
    }
    if method == "POST":
        headers["Content-Type"]="application/x-www-form-urlencoded"
    request = urllib.request.Request(BASE_URL + full_path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        try: detail = json.loads(body_text)
        except json.JSONDecodeError: detail = body_text[:500]
        category = "permission_denied" if exc.code == 403 else "authentication_failed" if exc.code == 401 else "rate_limited" if exc.code == 429 else "api_error"
        raise ThreeCommasEndpointError(path, category, f"3Commas HTTP {exc.code}: {detail}", exc.code) from exc
    except urllib.error.URLError as exc:
        raise ThreeCommasEndpointError(path, "network_or_outage", f"3Commas connection failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ThreeCommasEndpointError(path, "timeout", "3Commas request timed out.") from exc


def signed_get(path: str, params: dict[str, Any], api_key: str, private_key) -> Any:
    return signed_request("GET", path, params, api_key, private_key)


def signed_read_post(path: str, params: dict[str, Any], api_key: str, private_key) -> Any:
    return signed_request("POST", path, params, api_key, private_key)


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


def pair_currencies(pair: Any) -> tuple[str | None, str | None]:
    text = pair_text(pair).upper().replace("-", "_").replace("/", "_")
    tokens = [t for t in text.replace(",", "_").split("_") if t]
    if len(tokens) < 2:
        return None, None
    quote_codes = {"USDT", "USD", "USDC", "BTC", "XBT", "ETH", "EUR"}
    if tokens[0] in quote_codes:
        return ("BTC" if tokens[0] in {"XBT", "XXBT"} else tokens[0], "BTC" if tokens[1] in {"XBT", "XXBT"} else tokens[1])
    if tokens[-1] in quote_codes:
        return ("BTC" if tokens[-1] in {"XBT", "XXBT"} else tokens[-1], "BTC" if tokens[0] in {"XBT", "XXBT"} else tokens[0])
    return tokens[0], tokens[-1]

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
    pair = pair_text(deal.get("pair") or deal.get("pairs"))
    quote_currency, base_asset = pair_currencies(pair)
    # 3Commas bought_amount is the acquired base-asset quantity. bought_volume is
    # the quote-currency cost basis. Never label base quantity as USDT capital.
    asset_quantity = to_float(first_value(deal, ("bought_amount", "base_amount", "reserved_base_coin")))
    quote_cost = to_float(first_value(deal, ("bought_volume", "quote_volume", "invested_quote_amount")))
    result: dict[str, Any] = {
        "bot_name": str(deal.get("bot_name") or deal.get("name") or "3Commas DCA deal"),
        "pair": pair, "quote_currency": quote_currency, "base_asset": base_asset,
        "status": deal_status(deal), "created_at": created,
        "profit_pct": to_float(first_value(deal, ("actual_profit_percentage", "profit_percentage"))),
        "completed_safety_orders": to_int(first_value(deal, ("completed_safety_orders_count", "completed_manual_safety_orders_count"))) or 0,
        "max_safety_orders": to_int(deal.get("max_safety_orders")),
        "active_safety_orders": to_int(first_value(deal, ("current_active_safety_orders_count", "active_safety_orders_count"))),
        "bot_id": to_int(deal.get("bot_id")),
        "allocated_asset_quantity": asset_quantity,
        "allocated_asset": base_asset,
        "capital_used_quote": quote_cost,
        "capital_currency": quote_currency,
        "capital_used": quote_cost,
        "placed_order_reserve": to_float(first_value(deal, ("reserved_quote_funds", "reserved_funds", "active_safety_order_capital"))),
    }
    if publish_mode == "full":
        result.update({
            "average_entry": to_float(first_value(deal, ("bought_average_price", "average_price", "base_order_average_price"))),
            "current_price": to_float(first_value(deal, ("current_price", "current_market_price", "last_price"))),
            "take_profit_price": to_float(first_value(deal, ("take_profit_price", "final_profit_price"))),
            "profit_usd": to_float(first_value(deal, ("actual_usd_profit", "usd_profit", "actual_profit"))),
        })
    return result



def amount_value(value: Any) -> float | None:
    if isinstance(value, dict):
        return to_float(value.get("amount"))
    return to_float(value)


def sanitise_balance(row: dict[str, Any]) -> dict[str, Any]:
    code=str(row.get("currency_code") or row.get("code") or "").upper()
    return {
        "currency": code,
        "equity": to_float(first_value(row,("equity","position"))),
        "available": to_float(first_value(row,("position_available","available","available_long"))),
        "on_orders": to_float(first_value(row,("on_orders","on_orders_with_leverage"))) or 0.0,
        "usd_value": to_float(row.get("usd_value")),
        "current_price_usd": to_float(row.get("current_price_usd")),
        "account_id": to_int(row.get("account_id")),
    }


def sanitise_account(account: dict[str, Any], detail: dict[str, Any] | None = None, balances: list[dict[str, Any]] | None = None, balance_observed_at: str | None = None, balance_cached: bool = False) -> dict[str, Any]:
    merged=dict(account); merged.update(detail or {})
    clean_balances=[sanitise_balance(x) for x in (balances or []) if isinstance(x,dict)]
    total = amount_value(first_value(merged,("primary_display_currency_amount","usd_amount","total_usd_value","total_balance")))
    if total is None and clean_balances:
        vals=[x["usd_value"] for x in clean_balances if x.get("usd_value") is not None]
        total=sum(vals) if vals else None
    usdt=next((x for x in clean_balances if x.get("currency") in {"USDT","USDC","USD"}),None)
    free = usdt.get("available") if usdt else to_float(first_value(merged,("available_usdt","free_usdt","available_balance","balance")))
    return {
        "account_id": to_int(merged.get("id")),
        "name": str(merged.get("name") or merged.get("exchange_name") or "3Commas account"),
        "exchange_name": first_value(merged,("exchange_name","market_code","type")),
        "currency": "USDT",
        "total_usd_value": total,
        "free_usdt": free,
        "balance_records": len(clean_balances),
        "balances": clean_balances,
        "api_keys_state": merged.get("api_keys_state"),
        "balance_source": "3Commas ACCOUNTS_READ account info and account_table_data",
        "balance_observed_at": balance_observed_at,
        "balance_cached": bool(balance_cached),
    }

def load_previous_payload() -> dict[str, Any]:
    try:
        value=json.loads(OUTPUT_PATH.read_text(encoding="utf-8-sig"))
        return value if isinstance(value,dict) else {}
    except Exception:
        return {}

def previous_account_map(previous: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out={}
    for row in previous.get("accounts") or []:
        if isinstance(row,dict):
            aid=to_int(row.get("account_id"))
            if aid is not None: out[aid]=row
    return out

def age_minutes(value: Any) -> float | None:
    if not value: return None
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone(timezone.utc)
        return (datetime.now(timezone.utc)-dt).total_seconds()/60
    except Exception:
        return None

def cached_account(account: dict[str, Any], detail: dict[str, Any], previous_row: dict[str, Any], observed_at: str | None) -> dict[str, Any]:
    current=sanitise_account(account,detail,[],balance_observed_at=observed_at,balance_cached=True)
    for key in ("total_usd_value","free_usdt","balance_records","balances"):
        if key in previous_row: current[key]=previous_row.get(key)
    current["balance_source"]="Cached recent 3Commas ACCOUNTS_READ balance snapshot (quota guard)"
    return current

def success_timestamp(previous: dict[str, Any], status: str, attempted_at: str) -> str | None:
    if status in {"ok", "partial"}:
        return attempted_at
    return previous.get("last_success_at") or previous.get("generated_at")

def endpoint_result(path: str, status: str, category: str, message: str, http_status: int | None = None, records: int | None = None) -> dict[str, Any]:
    return {"path": path, "status": status, "category": category, "message": message, "http_status": http_status, "records": records, "observed_at": now_iso()}

def empty_payload(status: str, message: str, publish_mode: str = "masked", endpoints: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": VERSION, "authentication": "RSA self-generated", "generated_at": now_iso(),
        "last_attempt_at": now_iso(), "last_success_at": None,
        "status": status, "message": message, "publish_mode": publish_mode, "read_only": True,
        "endpoint_diagnostics": endpoints or {}, "accounts": [], "assets": {},
    }

def attempt_endpoint(name: str, path: str, params: dict[str, Any], api_key: str, private_key, endpoints: dict[str, Any], method: str = "GET") -> Any | None:
    try:
        value=signed_request(method,path,params,api_key,private_key)
        records=len(value) if isinstance(value,list) else None
        endpoints[name]=endpoint_result(path,"pass","ok","Endpoint completed successfully.",records=records)
        return value
    except ThreeCommasEndpointError as exc:
        endpoints[name]=endpoint_result(path,"fail",exc.category,str(exc),exc.http_status)
        return None
    except Exception as exc:
        endpoints[name]=endpoint_result(path,"fail","unexpected_error",f"{type(exc).__name__}: {exc}")
        return None


def main() -> int:
    previous = load_previous_payload()
    attempted_at = now_iso()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    tcfg = config.get("threecommas", {})
    publish_mode = str(tcfg.get("publish_mode", "masked")).lower()
    if publish_mode not in {"masked", "full"}: publish_mode = "masked"
    api_key=os.getenv("THREECOMMAS_API_KEY","").strip(); private_key_b64=os.getenv("THREECOMMAS_RSA_PRIVATE_KEY_B64","").strip()
    if not api_key or not private_key_b64:
        payload=empty_payload("not_configured","Add THREECOMMAS_API_KEY and THREECOMMAS_RSA_PRIVATE_KEY_B64 as GitHub Actions secrets.",publish_mode)
        payload["last_attempt_at"]=attempted_at; payload["last_success_at"]=previous.get("last_success_at") or previous.get("generated_at")
        OUTPUT_PATH.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2));return 0
    endpoints: dict[str, Any]={}
    try:
        private_key=load_private_key(private_key_b64)
    except Exception as exc:
        payload=empty_payload("error",str(exc),publish_mode,{"key":endpoint_result("local","fail","private_key_invalid",str(exc))})
        payload["last_attempt_at"]=attempted_at; payload["last_success_at"]=previous.get("last_success_at") or previous.get("generated_at")
        OUTPUT_PATH.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2));return 1
    validation=attempt_endpoint("validate","/public/api/ver1/validate",{},api_key,private_key,endpoints)
    authenticated=isinstance(validation,dict) and validation.get("valid") is True
    if not authenticated and endpoints.get("validate",{}).get("status")=="pass":
        endpoints["validate"]=endpoint_result("/public/api/ver1/validate","fail","authentication_failed",f"Validation response was not valid: {validation}")
    # Probe every approved read endpoint independently so one denied permission does not hide other evidence.
    accounts_raw=attempt_endpoint("accounts","/public/api/ver1/accounts",{},api_key,private_key,endpoints)
    bots_raw=attempt_endpoint("bots","/public/api/ver1/bots",{"limit":100,"offset":0},api_key,private_key,endpoints)
    deals_raw=attempt_endpoint("deals","/public/api/ver1/deals",{"scope":"active","limit":1000,"offset":0,"order_direction":"desc"},api_key,private_key,endpoints)
    for name,value in (("accounts",accounts_raw),("bots",bots_raw),("deals",deals_raw)):
        if value is not None and not isinstance(value,list):
            endpoints[name]=endpoint_result(endpoints[name]["path"],"fail","response_shape",f"Expected list, received {type(value).__name__}.")
    accounts_raw=accounts_raw if isinstance(accounts_raw,list) else [];bots_raw=bots_raw if isinstance(bots_raw,list) else [];deals_raw=deals_raw if isinstance(deals_raw,list) else []
    account_outputs=[]
    previous_accounts=previous_account_map(previous)
    try: balance_refresh_minutes=max(15,int(os.getenv("THREECOMMAS_BALANCE_REFRESH_MINUTES","1440")))
    except ValueError: balance_refresh_minutes=1440
    capital_provider=os.getenv("CRM_CAPITAL_PROVIDER","").strip().upper()
    direct_capital_configured=(capital_provider in {"LOCAL_KUCOIN","KUCOIN_DIRECT"}) or all(os.getenv(x,"").strip() for x in ("KUCOIN_API_KEY","KUCOIN_API_SECRET","KUCOIN_API_PASSPHRASE"))
    for account in accounts_raw:
        if not isinstance(account,dict): continue
        account_id=to_int(account.get("id"))
        if account_id is None:
            account_outputs.append(sanitise_account(account,balance_observed_at=attempted_at)); continue
        # Preserve scarce Starter-plan quota for the balance-table request.
        # The accounts listing already supplies the identity fields CRM needs;
        # the optional per-account detail GET previously made the balance read
        # the sixth rapid request and repeatedly triggered HTTP 429.
        detail={}
        endpoints[f"account_{account_id}_details"]=endpoint_result(
            f"/public/api/ver1/accounts/{account_id}",
            "pass",
            "not_requested_quota_guard",
            "Optional account-detail request skipped to preserve quota for the read-only balance table.",
        )
        prev=previous_accounts.get(account_id) or {}
        prev_stamp=prev.get("balance_observed_at") or previous.get("generated_at")
        if direct_capital_configured:
            endpoints[f"account_{account_id}_balances"]=endpoint_result(
                f"/public/api/ver1/accounts/{account_id}/account_table_data",
                "pass","not_requested_direct_capital",
                "3Commas balance-table request skipped because KuCoin direct read-only capital data is configured."
            )
            account_outputs.append(cached_account(account,detail,prev,prev_stamp) if prev else sanitise_account(account,detail,[],balance_observed_at=None,balance_cached=False))
            continue
        prev_age=age_minutes(prev_stamp)
        can_cache=bool(prev.get("balances")) and prev_age is not None and prev_age < balance_refresh_minutes
        balance_name=f"account_{account_id}_balances"; balance_path=f"/public/api/ver1/accounts/{account_id}/account_table_data"
        if can_cache:
            endpoints[balance_name]=endpoint_result(balance_path,"pass","cached_quota_guard",f"Reused balance snapshot aged {prev_age:.0f} minutes to reduce 3Commas quota usage.",records=to_int(prev.get("balance_records")))
            endpoints[balance_name]["source_age_minutes"]=round(prev_age,1)
            account_outputs.append(cached_account(account,detail,prev,prev_stamp))
            continue
        balances=attempt_endpoint(balance_name,balance_path,{},api_key,private_key,endpoints,method="POST")
        if balances is not None and not isinstance(balances,list):
            endpoints[balance_name]=endpoint_result(balance_path,"fail","response_shape",f"Expected list, received {type(balances).__name__}.")
            balances=[]
        if balances is None and endpoints.get(balance_name,{}).get("category")=="rate_limited" and prev.get("balances"):
            endpoints[balance_name]["category"]="rate_limited_cached"
            endpoints[balance_name]["message"] += " Reused the most recent balance snapshot."
            endpoints[balance_name]["cached_records"]=to_int(prev.get("balance_records"))
            account_outputs.append(cached_account(account,detail,prev,prev_stamp))
        else:
            account_outputs.append(sanitise_account(account,detail,balances if isinstance(balances,list) else [],balance_observed_at=attempted_at,balance_cached=False))
    assets: dict[str, dict[str, list[dict[str, Any]]]]={}
    for bot in bots_raw:
        if not isinstance(bot,dict):continue
        asset=asset_from_pair(bot.get("pairs") or bot.get("pair"))
        if asset:assets.setdefault(asset,{"bots":[],"deals":[]})["bots"].append(sanitise_bot(bot))
    for deal in deals_raw:
        if not isinstance(deal,dict):continue
        asset=asset_from_pair(deal.get("pair") or deal.get("pairs"))
        if asset:assets.setdefault(asset,{"bots":[],"deals":[]})["deals"].append(sanitise_deal(deal,publish_mode))
    failed=[name for name,row in endpoints.items() if row.get("status")!="pass"]
    core_names={"validate","accounts","bots","deals"}
    core_failed=[name for name in core_names if endpoints.get(name,{}).get("status")!="pass"]
    core_status="ok" if not core_failed else "partial" if authenticated and (bots_raw or deals_raw or accounts_raw) else "error"
    status="ok" if not failed else "partial" if assets or accounts_raw or authenticated else "error"
    if core_status=="ok" and failed:
        message="Core bot/deal/account sync is healthy; one or more optional account-balance reads are limited."
    else:
        message="All read-only 3Commas endpoints updated successfully." if status=="ok" else f"Read-only sync completed with endpoint issues: {', '.join(failed)}."
    payload={"version":VERSION,"authentication":"RSA self-generated","generated_at":attempted_at,"last_attempt_at":attempted_at,"last_success_at":success_timestamp(previous,status,attempted_at),"status":status,"core_status":core_status,"core_failed":core_failed,"message":message,"publish_mode":publish_mode,"read_only":True,"endpoint_diagnostics":endpoints,"accounts":account_outputs,"assets":assets}
    OUTPUT_PATH.parent.mkdir(parents=True,exist_ok=True);OUTPUT_PATH.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
    # Partial data is publishable and actionable; only complete authentication failure fails the workflow.
    return 0 if status in {"ok","partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
