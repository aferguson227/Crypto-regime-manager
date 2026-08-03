# Crypto Regime Manager V7.1 — Automatic Research Experiments

V7.1 adds an automatic, one-variable Candidate B experiment for SUI while preserving TEL and TAO production monitoring.

## What the app does automatically

When SUI Candidate A fails the positive P&L, maximum trade duration, or profitable-window gate, the workflow:

1. diagnoses the unresolved or longest-risk condition;
2. creates SUI Candidate B;
3. changes one variable only;
4. replays A and B on the same observed KuCoin history;
5. publishes the comparison on the Research page;
6. labels the result as proposed, rejected, or ready for a manually approved forward comparison.

The first automatic hypothesis is:

> Candidate B adds: Low-regime entry requires close at or above EMA200.

Candidate B never replaces Candidate A automatically and never produces a live SUI recommendation.

## Important interpretation

Until Candidate B is manually approved with a new forward-test start date, its comparison is a post-hoc diagnostic. It may show whether the rule would have helped historically, but it is not independent validation.

## Manual approval

Approval is intentionally a configuration change. In `config.json`, find the SUI `research_experiments.candidate` section and set:

```json
"approved_for_forward_test": true,
"forward_test_start": "YYYY-MM-DDT00:00:00Z"
```

Use a date after the rule was reviewed. Commit the change and run the main workflow. From then on, Candidate B metrics are calculated only from that new start date.

Do not approve Candidate B merely because its diagnostic result looks better. Review its profit, drawdown, trade duration, trade count, and whether it blocks too many valid entries.
