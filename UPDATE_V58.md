# CRM V60.0.0 — Reliable Recovery & Deployment Lifecycle

V58 addresses the recurring V57 state where CRM displayed multiple dependent warnings while claiming to retry automatically without evidence of a recovery action.

## Transactional KuCoin recovery
CRM now runs one dependency-aware recovery transaction:
1. KuCoin account
2. KuCoin orders
3. KuCoin fills
4. execution reconciliation
5. realised-P/L accounting
6. live portfolio truth
7. trading safety verification
8. freshness/source health

Dependent warnings are suppressed while an upstream KuCoin incident is recovering. The dashboard reports only root causes.

## Truthful recovery
The Health panel now distinguishes:
- recovery action actually executed;
- root causes resolved this cycle;
- root causes remaining;
- consecutive unresolved cycles;
- automatic recovery versus genuine user action.

A recoverable issue becomes user-action-required only after repeated failed recovery cycles.

## Private KuCoin execution scope
Order/fill collection no longer queries the whole research registry. It queries assets with actual private-trading relevance: non-zero KuCoin balances, live trades, live production bots/deals, assets already present in the persistent fill ledger, plus TEL production. This prevents research-only/unlisted symbols from falsely degrading private order monitoring.

## Local Agent heartbeat
Long-running research modules update the Local Agent heartbeat while they are still running, preventing a healthy but lengthy background cycle from appearing stale.

## Deployment Lifecycle
CRM now publishes a governed provider-independent lifecycle:
RESEARCHING → VALIDATING → READY_FOR_DEPLOYMENT_REVIEW → READY_TO_DEPLOY → RECOMMENDED_NOW → ACTIVE

Fixing a Kraken continuation blocker does not itself create a trade signal. The candidate must still pass every deployment gate, have complete DCA settings, receive a capital allocation and win portfolio ranking.

## Bot setup access
The top Trading Briefing and Deployment Queue now provide direct access to:
- exact DCA settings;
- current lifecycle state;
- suggested allocation;
- entry trigger;
- blockers;
- whether manual deployment is currently permitted.

TEL live settings now include SO deviation, max active SOs and order type from the production 3Commas read-only profile where available.

## Safety
V58 still cannot place/cancel KuCoin orders or automatically create/start/edit 3Commas bots. Native direct execution remains HARD LOCKED.
