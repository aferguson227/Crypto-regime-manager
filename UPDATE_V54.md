# CRM V58.0.0 — Trading Command Centre & Native Execution Preparation

V54 reorganises CRM around the decisions that matter immediately when the application opens.

## Trading Command Centre
The first dashboard section now combines:
- current recommended strategy/action;
- total KuCoin-recognised portfolio value;
- capital available for another bot;
- capital protected for active DCA ladders;
- active trades;
- open, realised and total trading P/L;
- next asset recommended for capital;
- suggested next allocation.

## Ready for Deployment Review
Candidates that have completed all deployment gates are promoted beside the Trading Briefing near the top of the page. Their current regime, unseen KuCoin validation return, longest trade, drawdown, evidence grade and allocation are visible without navigating through the research sections.

## Portfolio Now
The former fragmented capital/live-trade views are consolidated into one user-facing portfolio view. Realised P/L uses the best available reconciled value and stops showing “calculating” once a recognised result exists.

## Trading & Execution
Technical provider language is replaced with:
- KuCoin connection;
- Trade protection;
- 3Commas monitoring;
- CRM direct trading;
- migration progress;
- test trading plans;
- Kraken → KuCoin follow-up.

3Commas remains secondary transition telemetry. KuCoin remains authoritative.

## Freshness redesign
Clock age alone no longer creates a false `Source overdue`.
- Healthy Local Agent + older unchanged published value = Updating.
- 3Commas delay = Provider degraded, not global failure.
- Website publication delay is independent of trading-data reliability.
- Action Required is reserved for an actual critical collector failure or when both KuCoin data and the Local Agent heartbeat are too old.

## Navigation
The duplicate Bots / Market / System / Engineering top tabs are removed from the primary navigation. The normal product surface is the Dashboard; deeper system information is available under Advanced.

## System checks
“Automatic diagnostics: Healthy · Quick” becomes the simpler user-facing “System checks: Healthy”. Diagnostic mode remains available only for troubleshooting.

## Direct KuCoin migration
A new migration-progress engine makes the transition away from 3Commas visible. It tracks balance access, order access, fill-ledger readiness, trade-protection checks, CRM test plans and restart-safe order identity. Guarded live trading remains deliberately locked.

## Safety
V54 is still read-only for live execution. It cannot place or cancel a KuCoin order and cannot modify/start/stop a 3Commas bot.
