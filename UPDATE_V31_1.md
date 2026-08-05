# Crypto Regime Manager V31.1.0 — Research Intelligence

## Included

- Fixes the GitHub Actions `cannot pull with rebase: You have unstaged changes` failure.
- Synchronises before refresh, stages all published outputs, and retries pushes safely.
- Gives the cloud refresh and 3Commas workflows one shared publishing queue.
- Adds regime screening, strategy-family comparison, walk-forward degradation analytics, local DCA sensitivity grids, and a generated research report.
- Adds `Research intelligence` under More tools.
- Preserves read-only safeguards and manual approval.
- Adds a lock-aware installer with retries and a rollback backup.

## Important interpretation

Strategy-family scores and DCA sensitivity cells are screening diagnostics. They do not replace an independent fee-aware backtest or forward validation. No live bot is created or changed.
