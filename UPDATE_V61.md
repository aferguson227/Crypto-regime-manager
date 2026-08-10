# CRM V66.0.0 — Operational State Repair & DCA Specification

V61 fixes the stalled V60 state where KuCoin account/order collectors could be current while the Local Agent heartbeat remained many hours overdue, realised-P/L backfill stayed at 24/25 weeks, and System Health preserved a stale credential incident.

## Fast operational refresh is now independent
The 15-minute Local Agent no longer runs the heavyweight research scheduler. It refreshes private KuCoin truth, fills, accounting, portfolio, trade protection, freshness and lightweight decision outputs.

Heavy market scanning/backtesting/walk-forward research runs in a separate hidden `CryptoRegimeManager-ResearchWorker` task every six hours with its own execution window. It uses an isolated source copy and exports a research snapshot to persistent CRM_Data, which the fast Local Agent imports safely on its next cycle.

This means a six-hour optimisation run can no longer make the 15-minute trading heartbeat appear dead or prevent realised-P/L backfill from advancing.

## KuCoin last-good truth
Successful read-only KuCoin account snapshots are persisted outside Git. If a non-credentialed diagnostics/build process later runs, it cannot erase valid private trading truth. A missing credential environment in that secondary process produces a `fallback_current` state using the last good snapshot rather than a false account outage.

The recovery controller only retries private KuCoin endpoints when the current process actually contains the local credentials.

## Local Agent freshness
The dashboard Local Agent age now uses `heartbeat_at`/`completed_at`, not an older generated snapshot timestamp. The schedule-health output reports the fast Local Agent and isolated Research Worker separately.

## Realised-P/L backfill
The lightweight fill-ledger/cost-basis job remains in every 15-minute operational cycle. Once the final weekly window is searched it either calculates complete realised P/L or preserves an explicit unmatched-cost-basis diagnostic; it no longer waits behind long backtesting work.

## DCA deployment specification
V61 begins DCA Optimisation 2.0 by producing a complete provider-independent setup from each frozen KuCoin winner:
- BO and SO sizing used by the current backtest engine;
- TP;
- SO deviation;
- safety-order count;
- volume scale;
- step scale;
- max active safety orders;
- max active deals;
- validated entry trigger/manual CRM signal;
- order-type policy;
- trailing;
- cooldown.

Research-tested settings and governed execution defaults are labelled separately. V61 deliberately does not pretend BO/SO sizing was optimised: current 100/100 USDT sizing is preserved because that is what the existing replay engine actually validated.

The Deployment Queue now separates `Capital required` from `Safe allocation now`. A candidate can therefore remain technically valid while TEL's active DCA reserve leaves no capital currently safe for a second live bot.

## Safety
Native KuCoin order placement/cancellation remains HARD LOCKED. V61 creates no live orders and does not automatically create/edit/start/stop 3Commas bots.
