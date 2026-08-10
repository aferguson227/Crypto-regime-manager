# Crypto Regime Manager V64.0.0 — Autonomous Candidate Discovery, Persistent Research & Professional Operations UI

## Persistent research memory
V49 introduces a SQLite research database outside Git under `C:\Crypto\CRM_Data\Research\crm_research.db`.
Known assets, cache fingerprints, research runs, candidate states and recommendation evidence survive application upgrades.

## Smart backtest cache
The background scheduler fingerprints KuCoin datasets plus research policies. If nothing material changed, previous
research is reused. Full optimisation is re-run only when new evidence/policy changes invalidate the cache or periodic
revalidation is due.

## Autonomous KuCoin discovery
The scheduler refreshes the wider KuCoin USDT universe hourly, ranks eligible markets, places promising assets into
bounded historical acquisition, and progresses them through KuCoin regime/DCA research and frozen walk-forward
validation. BTC-quoted research remains experimental/read-only.

## Fast installation
V49 installers migrate the research database and validate the research engines, but do not run the expensive 100k+
optimisation loops synchronously. Research resumes in the silent Local Agent after installation.

## Git State Recovery Guard
Interrupted rebase/merge/cherry-pick operations are auto-recovered only when every unmerged path is declared generated
runtime state. Any source/unclassified conflict stops for manual review.

## Professional Operations UI
- universal internal-enum formatting removes visible underscore-delimited states;
- sentence-style status labels retain proper acronyms such as BTC, USDT, DCA, P/L and KuCoin;
- Decision Readiness shows individual passed/outstanding gates;
- Validation-open positions show the continuation-resolution state;
- a top-level “What CRM is doing” strip shows scan, history, backtest, ready, live and staged activity;
- Design System 2.0 improves spacing, typography, cards and phone/shared-window layouts;
- Presentation Quality Gate prevents known raw-state leaks.

## Portfolio groundwork
V49 adds advisory allocation recommendations based on deployable capital and a governed cash buffer. It remains
manual/read-only. Automatic deployment and diversification/correlation allocation remain future gated phases.

## Safety
V49 does not create, edit, start or stop bots and does not place orders. Live deployment remains manual.
