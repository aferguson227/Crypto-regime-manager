# CRM V67.0.0 — Managed Bot Portfolio & Paper Trading

V67 moves CRM from a deployment queue toward a managed strategy portfolio.

## My Bots
- New **My Bots** section near the top of the dashboard.
- Live production bots appear automatically.
- Any DCA-optimised deployment candidate can be added with **Add to My Bots**.
- My Bots displays state, position size, safety-order progress, P/L, reserve/capital requirement and next action.
- Opening a live bot now shows its current deal state/settings rather than incorrectly presenting a deployment-readiness warning.

## Forward paper trading
- Exact unseen-validated DCA configurations are paper traded continuously against current KuCoin prices.
- Paper state persists outside Git under CRM_Data and survives upgrades.
- Paper trades model BO, DCA safety fills, volume/step scaling, TP exits and 0.1% fees.
- Paper evidence accumulates even when conservative safe capital is 0, giving CRM genuine forward evidence before a live deployment.
- No exchange or 3Commas write endpoint is used.

## Shared-capital intelligence
- Portfolio allocation now incorporates historical unseen validation, drawdown, capital lock, diversification and forward-paper evidence.
- Conservative `safe_multi_bot_pool_usdt` remains the live deployment gate.
- Conditional capacity remains advisory only.
- Candidate ranking never bypasses capital safeguards.

## Live bot state
- Current production rows include position cost, average entry, completed/max/active SOs, remaining DCA reserve and current mark-to-market P/L.
- Continuous strategy revalidation answers whether CRM would still choose the live strategy today, while never changing an active deal mid-trade.

## Resident KuCoin service reliability
- Stale PID lock files self-heal.
- Each child collector has a timeout so one hung KuCoin request cannot freeze the resident service.
- Heartbeat is written while modules are running, not only at the end of a full cycle.
- A bounded local diagnostic log is retained.
- System Health validates the actual heartbeat as well as the HKCU startup registration.
- Recovery restarts the per-user service directly and no longer tells the user to restart an obsolete scheduled LiveDataService task.

## Dashboard
- Trading Briefing is more concise: Portfolio, Cash, DCA Reserve, Deployable Capital and combined Trading P/L.
- My Bots carries the detailed per-bot operational state.
- Deployment blockers name the actual missing evidence/capital requirement rather than a generic “one or more gates” message.

Native KuCoin live order placement/cancellation remains HARD LOCKED.
