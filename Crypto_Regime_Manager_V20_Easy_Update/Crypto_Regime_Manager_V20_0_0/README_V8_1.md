# Crypto Regime Manager V8.1

V8.1 is a reliability and research-quality update to the Strategy Evolution Engine.

## Fixes and improvements

- Adds the missing `itertools` import required for combination testing.
- Replaces misleading trade-retention percentages above 100% with baseline deal count, candidate deal count, and deal-count change.
- Clusters hypotheses that produce effectively identical results.
- Uses one representative from each equivalent-result cluster when generating combinations.
- Shows correlated-rule clusters on the Evolution page.
- Keeps all production strategies, market data, and 3Commas integration unchanged.

All evolution outputs remain post-hoc research evidence and require manual approval plus a new forward-test start date.
