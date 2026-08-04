# Crypto Regime Manager V25.0.0

## Autonomous infrastructure

- Scheduled GitHub Actions refresh every four hours, independent of the user’s laptop.
- Existing replay, health, discovery and forward-validation pipelines run from one cloud entry point.
- `docs/cloud_status.json` records running, healthy or error state after every attempt.
- Dashboard pages check for a newly published snapshot every five minutes and when the app regains focus.
- A new Cloud Refresh page explains scheduler state and safeguards.
- Publishing retries transient Git conflicts before reporting failure.

## Safeguards

V25 remains read-only and advisory. It does not change live bots, DCA parameters, entry rules or production settings. Manual approval remains required.
