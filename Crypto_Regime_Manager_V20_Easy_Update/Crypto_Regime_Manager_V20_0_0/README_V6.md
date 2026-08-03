# Crypto Regime Manager V6 — Trading Intelligence

V6 adds a transparent opportunity-ranking layer above the existing TEL and TAO regime, entry, replay, health and read-only 3Commas systems.

## New features

- Portfolio summary with the best currently eligible setup
- Opportunity score from 0–100 for each coin
- Clear `WAIT`, `CAUTIOUS`, `CANDIDATE`, or `STRONG CANDIDATE` status
- Plain-English positive factors and cautions
- Dedicated `docs/intelligence.html` page
- Combined maximum theoretical capital and replay-position count

The opportunity score is not a probability of profit. Entry permission remains absolute: a blocked setup always stays `WAIT` regardless of its health score.

## Upgrade

Copy the package contents over the existing repository, but preserve the latest files in `data/`. Commit and push, then run both GitHub Actions workflows once.
