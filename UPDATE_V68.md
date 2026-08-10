# CRM V68.0.0 — Portfolio Command & Reliability

## Dashboard hierarchy
- Today’s Trading Briefing is now portfolio-level only: Portfolio, Cash, DCA Reserve, Deployable Capital and Trading P/L.
- Redundant Live Position and Next Opportunity cards are removed.
- My Bots is the operational centre for live and paper-managed strategies.
- A strategy added to My Bots is removed from the normal Deployment Queue to avoid duplication.

## My Bots
- Adds Regime and CRM Decision columns.
- Live rows retain position, DCA progress, P/L and reserve.
- Paper rows retain capital need and forward P/L.
- The highest-ranked managed paper strategy becomes Next Capital Priority inside My Bots.
- Live strategy revalidation never changes an active deal mid-trade.

## Forward paper evidence
Paper strategies now accumulate:
- forward open/realised P/L;
- closed deals;
- win rate;
- time under paper observation;
- profit per day;
- maximum drawdown;
- DCA safety-order usage.

## Evidence-driven System Health
- A failed background order/fill collector no longer escalates to user Action Required merely because retries continue.
- CRM first checks whether resident-service heartbeat, current portfolio truth, current pricing and account truth remain fresh.
- If decision-critical truth is fresh, collector recovery is shown as a low-severity background refresh and trading decisions remain usable.
- Genuine stale or unavailable decision-critical truth still escalates.

## Installer architecture
V68 inherits the integrated preflight/troubleshooter introduced in corrected V67:
pause writers → diagnose → safe runtime cleanup → install → test → publish → restart → post-install checks.

## Execution safety
Direct CRM KuCoin order placement/cancellation remains HARD LOCKED.
