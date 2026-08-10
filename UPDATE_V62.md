# CRM V62.0.0 — Accounting Completion, Continuation Resolution & DCA Optimisation Gate

V62 addresses the remaining V61 limitations around legacy realised-P/L cost basis, unresolved Kraken-open continuation evidence, deployment readiness and the distinction between optimised DCA settings and governed execution defaults.

## Targeted deep realised-P/L cost-basis search
After the normal 180-day fill-history scan completes, CRM now searches only the affected unmatched asset further back rather than rescanning the whole account. The deep search:
- is restricted to unmatched sell assets;
- searches in KuCoin-compatible weekly windows;
- persists a per-asset cursor;
- searches up to 730 days;
- runs up to 12 weekly windows per 15-minute Local Agent cycle;
- publishes deep-search progress and an ETA.

If the acquisition still cannot be found after the bounded deep search, CRM publishes the exact unmatched sell limitation instead of inventing a cost basis or remaining stuck indefinitely.

## Automatic Kraken Q1 evidence materialisation
Older CRM releases preserved the Kraken walk-forward registry but did not always preserve the normalized Q1 candle file required to reconstruct an open validation position.

The isolated Research Worker now:
1. identifies Kraken validation cases that ended open;
2. looks first in persistent CRM_Data;
3. automatically checks `CRM_KRAKEN_VALIDATION_DIR`;
4. checks `C:\Crypto\Kraken Data\Q1_2026.zip`;
5. normalizes only the required assets to 4-hour candles;
6. persists the normalized evidence outside Git.

The original Kraken PASS/FAIL is never rewritten.

## Kraken → KuCoin continuation resolution
Continuation now reports exactly which stage is blocking:
- Kraken evidence materialising;
- KuCoin history acquiring;
- KuCoin history does not reach cutoff;
- KuCoin continuation gap;
- replay discrepancy;
- still open;
- closed later on KuCoin.

KuCoin coverage records first/last candle, post-cutoff bars and the gap between the Kraken cutoff and first comparable KuCoin candle. The continuation engine reruns in the same research cycle after new KuCoin history is acquired.

A later KuCoin closure removes the cutoff-data blocker but does not turn the original Kraken FAIL into PASS. Kraken remains an independent robustness penalty rather than an automatic veto once the continuation is resolved.

## DCA Optimisation 2.0
The existing KuCoin engine already optimises entry trigger, TP, SO deviation, ladder depth, volume scale and step scale on training data before freezing those settings for unseen validation.

V62 adds training-only BO/SO sizing optimisation over a bounded sizing grid. The winning sizing is frozen and tested on unseen KuCoin validation.

Only settings that have completed that pipeline are displayed as **Recommended DCA Settings**.

Execution controls that are not represented in the replay model — max concurrent SOs, max active deals, order policy, trailing and cooldown — are clearly shown as governed execution controls and are never called optimised.

If optimisation is incomplete, the dashboard says **DCA setting optimisation in progress** and withholds an exact recommended setup.

## Deployment lifecycle
The deployment queue now explicitly includes:
- DCA optimisation status;
- continuation-resolution status;
- capital required by the validated setup;
- safe allocation currently available.

A candidate reaches Ready to Deploy only when:
- mandatory research evidence passes;
- DCA optimisation is complete;
- unresolved Kraken-open continuation is resolved;
- safe available capital is sufficient.

## System Health separation
System Health now counts only application, collector, freshness and live-trade safety faults. Historical accounting limitations and research/deployment uncertainty are displayed as operational notes in their relevant sections and do not inflate `Root issues remaining`.

## Safety
CRM remains read-only for native KuCoin execution. V62 cannot place/cancel exchange orders or create/start/edit/stop 3Commas bots automatically.
