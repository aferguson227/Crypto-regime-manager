# V33.0.3 - Operational Stability

- Separates versioned release diagnostics from runtime diagnostics.
- Regenerates release metadata and snapshots before acceptance tests.
- Adds independent 3Commas and application-cloud freshness reporting.
- Reports last attempt, last successful sync, endpoint status, and failure classification.
- Prevents routine diagnostics runs from dirtying the Git working tree.
- Preserves strict read-only 3Commas access and manual approval.
