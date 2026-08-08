# Crypto Regime Manager V45.0.0 — Regime-Aware Backtesting & Explainable Operations

V45 turns background research into a governed automatic process and makes every major dashboard status explain itself.

## Research engine
- Tests seven market-entry trigger families.
- Optimises DCA TP, SO deviation, ladder depth, volume scale and step scale by regime.
- Scores return together with drawdown, trade frequency and capital lock duration.
- Longest closed trades above 7 days are penalised; open positions receive stronger penalties and 30-day unresolved research positions are rejected by default.
- Uses training-only optimisation, freezes settings, and preserves independent validation as a separate gate.
- Current KuCoin/global regime is a forward context gate, not a source for hindsight curve fitting.

## Explainable operations
- Refresh age uses Current / Refresh due / Overdue / Action required. Age alone is not called Attention.
- Global regime publishes each criterion, weight and score contribution.
- XBT and XXBT are normalised to BTC when searching Kraken evidence.
- Breadth explains the numerator and universe when known.
- Recommendation percentages are labelled Confidence; historical returns are separately labelled.
- Recommended Bot cards explain what Add to Recommended does and the next workflow stage.
- Longest closed trade and validation-ended-open-position are visible.
- Suggested initial allocation uses current deployable capital when available.
- A Background Research summary shows what CRM is testing automatically.

## Automation
- Local Agent continues every 15 minutes and autonomous diagnostics run on every cycle.
- Expensive regime research is cached and normally re-runs every 24 hours or when its input data changes.
- Future installers run the Local Agent once automatically after a successful installation; a refresh failure does not roll back a valid release.

## Safety
Research and trading remain read-only/advisory. Manual approval remains required for live deployment.
