# CRM V66.0.0 — KuCoin Reliability & Unified Trading Briefing

V57 addresses the root cause behind the recurring KuCoin/order/freshness/safety warning cascade.

## Symbol-aware KuCoin order monitoring
The previous `/api/v1/hf/orders/active` account-wide call could be rejected with `Symbol can't be empty`.
V57 derives a bounded relevant USDT symbol scope from KuCoin balances, live trades, production bot profiles, deployment candidates and the coin registry, then queries current KuCoin HF Spot order endpoints per symbol.

Active orders use `/api/v1/hf/orders/active/page`; recent completed orders use `/api/v1/hf/orders/done`. Both remain General/read-only.

## Symbol-aware KuCoin fill history
The same relevant-symbol scope is used for `/api/v1/hf/fills`.
This removes reliance on an empty-symbol request and should allow recent TEL fills to enter the persistent local ledger for independent realised-P/L accounting.

## Region/base handling
CRM uses the configured KuCoin API base first, then the global `api.kucoin.com`. The EU endpoint is no longer tried automatically unless an explicit region-fallback flag is enabled. An invalid request is classified as an invalid request rather than being misreported as an authentication failure.

## Local Agent heartbeat
The Local Agent now writes a heartbeat at startup and throughout each module cycle, plus a completion timestamp. Long research cycles should therefore no longer make a healthy running agent look one hour old.

## Root-cause health incidents
Health & Recovery collapses dependent symptoms. If KuCoin order monitoring is the root cause, freshness and trading-safety uncertainty are shown as consequences of that incident rather than three additional Action required warnings.

A recoverable condition is now `Recovering automatically`. `Action required` is reserved for failures that genuinely need the user.

## Dashboard de-duplication / rebrand
The duplicated “Autonomous Trading Operations Centre” introduction is removed.
The application header is now simply:
- Crypto Regime Manager
- Trading Dashboard

Today’s Trading Briefing remains the single primary decision summary.

## Trading & Execution
KuCoin status is split into:
- KuCoin balances
- KuCoin orders
- KuCoin trade history

This makes it clear which read-only API capability is healthy/recovering.

## 3Commas migration
The migration continues without rushing the write path. KuCoin is authoritative state; 3Commas remains the live execution provider during transition; CRM native execution remains hard-locked while order/fill accounting and shadow parity are proven.
