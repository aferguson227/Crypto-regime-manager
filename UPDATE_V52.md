# Crypto Regime Manager V53.0.0 — Execution Assurance & Provider Independence

V52 accelerates the move away from 3Commas as the operational source of truth.

## Execution Assurance
- KuCoin order state, fills and reconciled position state are canonical.
- 3Commas is secondary provider telemetry.
- CRM verifies TP protection, safety-order presence, orphan orders and provider/exchange lifecycle mismatches.
- A provider-suspended/stale trade cannot override proven KuCoin truth.
- Missing protection becomes an explicit execution failure rather than a generic provider warning.

## Native KuCoin execution readiness
- CRM now carries a locked native Spot execution contract with deterministic `clientOid` generation, order validation, kill-switch semantics and idempotency design.
- The verified future Spot endpoints are recorded in the readiness snapshot.
- V52 cannot place or cancel a live order: both gateway methods intentionally raise a hard live-order lock.
- Shadow parity and restart-safe order identity are the prerequisites for the later guarded direct-execution release.

## Candidate evidence grades
Every candidate now shows:
- KuCoin 4h history start/end;
- history years and bar count;
- regime-profile count;
- evidence grade: Screen only / Preliminary / Deployment research / High confidence;
- unseen KuCoin walk-forward status;
- optional Kraken robustness.

Short-history assets cannot reach normal deployment approval merely because a short backtest looks strong.

## Kraken → KuCoin continuation acquisition
Assets whose frozen Kraken validation ended open are placed in a high-priority KuCoin history-acquisition queue until the later continuation period can be tested. The original Kraken result remains frozen.

## Decision-impact freshness
`Source overdue` can now be raised only by stale/failed decision-critical KuCoin or Local Agent truth.
A stale 3Commas feed produces `Partially degraded` while current KuCoin truth remains usable.
Pages publishing is reported separately as Publishing/Publication delayed rather than making exchange truth look stale.

## Dashboard
A new Execution Control area shows KuCoin order truth, execution assurance, 3Commas' secondary role, native-execution readiness, shadow plans and continuation-acquisition work.

## Safety
No live order, cancellation, bot mutation or automatic deployment is enabled in V52.
