# Crypto Regime Manager V58.0.0 — Portfolio & Execution Intelligence

V51 moves exchange truth and multi-bot portfolio decisions ahead of execution-provider telemetry.

## KuCoin ↔ 3Commas reconciliation
- Collects recent KuCoin open/closed Spot order state with General/read-only permission.
- Detects a 3Commas deal that remains open after KuCoin proves a matching position-size exit completed.
- Marks the provider deal stale, warns that it may block the next entry, excludes it from CRM active-trade/capital truth, and surfaces it in Decision Inbox.
- No deal cancellation or order mutation is performed.

## Canonical live portfolio and coin lifecycle
- Live Portfolio uses exchange-reconciled position truth.
- Capital reserve excludes provider-stale deals proven closed on KuCoin.
- Coin lifecycle gives execution state precedence over research labels: TEL can be Live production while forward research continues.
- Lifecycle is separate from research state.

## Kraken → KuCoin continuation
For Kraken validation runs that ended open, CRM deterministically reconstructs the frozen unresolved Q1 position from the original validation data and continues only that position using later KuCoin 4h candles. Closure time, total duration, final P/L and maximum adverse P/L are reported separately. The original Kraken result is never rewritten.

## Candidate decision evidence
Deployment Candidate review now includes KuCoin validation return/P&L, forward-observation return, closed deals, average/P90/longest hold, drawdown, historical annualised equivalent (clearly labelled non-forecast), adaptive-research stage progress and estimated remaining background cycles.

## Regime-specific bot profiles
Each live/researched asset can retain separate validated Bull, Accumulation, Neutral and Bear profiles. The Dashboard shows the profile selected for the current regime; unvalidated regimes explicitly mean no automatic new entry.

## Multi-bot portfolio allocation
The advisory allocator considers current live-bot slots, deployable KuCoin capital, cash buffer, validation return, drawdown, capital-lock duration and correlation to live bots. It proposes allocations only for candidates whose non-capital research gates have passed.

## Shadow execution
Ready candidates receive a hypothetical DCA order ladder for comparison with 3Commas behaviour. Shadow plans call no live order endpoint. Prepare deployment remains a browser-local manual review state.

## Professional presentation
"Staged / Recommended Bots" becomes "Deployment Candidates"; "Recommended Bots" becomes "Research Candidates". A DOM-wide presentation adapter prevents raw underscore-delimited machine enums from appearing on any published page. The release gate scans all HTML pages for raw machine enums.

## Safety
V51 is read-only. It does not create/edit/start/stop 3Commas bots, cancel stale deals, or place KuCoin orders.
