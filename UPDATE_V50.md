# Crypto Regime Manager V60.0.0 — Decision Workflow, Adaptive Research & Live Accounting

V50 turns V49's autonomous research into an explainable decision workflow.

## Decision workflow
Every researched candidate receives five visible gates: historical data, unseen KuCoin walk-forward, trade fluidity,
current-regime fit and capital allocation. Staged candidates show monitoring progress and an expandable Review candidate
panel. "Prepare deployment" records approval for a future manual execution review only; it does not start a bot.

## Adaptive failed-candidate research
Candidates that fail because of unresolved exposure, drawdown, long trades or cross-exchange instability are diagnosed
and queued for bounded follow-up experiments. Expanded DCA/search settings are applied only during training and every
new winner must re-pass unseen KuCoin validation. Frozen failed results are never rewritten.

## KuCoin realised-P/L ledger
V50 adds read-only `GET /api/v1/hf/fills` collection using the existing KuCoin General/read-only credentials. Recent fills
are persisted under `C:\Crypto\CRM_Data\Accounting\kucoin_fills.db`, so cost-basis coverage grows across upgrades.
Realised P/L is published only when sell fills can be matched to known cost basis; partial history is clearly labelled.

## Freshness and publication truth
Website publication age is informational when live Pages is synchronised. Refresh View reports the current published
snapshot while individual collector freshness remains visible. Cloud Watchdog distinguishes decision-blocking failures
from non-blocking telemetry age.

## Professional presentation
Canonical relative timestamps use forms such as `8h 2m ago`, machine enums are converted to sentence-style labels with
correct acronyms, and staged review cards are responsive on desktop/shared-window/mobile layouts.

## Capital allocation
The Dashboard falls back to the next governed candidate's advisory allocation calculated from canonical deployable
capital. Unknown remains possible only when fresh capital truth itself is unavailable.

## Safety
V50 remains read-only and manual-control. It does not create/edit/start/stop bots and does not place orders.
