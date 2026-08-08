# V46 Dashboard Recovery Hotfix

This hotfix does not change the V46 application version.

Root cause:
- V46 Live Portfolio called `CRMFormat.money()`, but the canonical formatter did not define that function.
- The resulting JavaScript exception stopped execution before Expansion Readiness, Recommended Bots,
  Background Research, Recommendation Timeline, Coin Registry, Recommendation History and Global Market rendered.
- The V46 overflow guard also tied value font sizing too aggressively to viewport width.

Fix:
- Adds formatter compatibility and uses canonical quote formatting.
- Isolates late dashboard widgets so one failure cannot blank the rest of the page.
- Uses card-aware grid layout and targeted text fitting.
- Aligns the health/status badge with Refresh.
- Clarifies that Expansion Readiness is a gate summary, not the backtest engine.
