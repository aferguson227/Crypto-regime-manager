# V32.7.0 — Cloud Reliability & Portfolio Intelligence

V32.7 adds endpoint-by-endpoint read-only 3Commas diagnostics, workflow freshness monitoring, GitHub Actions self-checks and portfolio-level capital, overlap and next-allocation intelligence. Manual approval remains mandatory and no live trading mutation capability is introduced.

## Key safeguards
- Only approved GET endpoints are available to the 3Commas integration.
- Permission failures are published per endpoint without hiding successful evidence.
- Application updates do not require routine manual workflow runs.
- Portfolio allocation is advisory and unknown capital is never invented.
