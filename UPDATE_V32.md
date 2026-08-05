# V32.0.0 — Deployment Intelligence Foundations

This build completes the Phase 1 baseline stabilisation work and begins the operating-state foundation without enabling deployment recommendations or any automated 3Commas action.

## Included
- One canonical release identity in `app/release.json`.
- Standard package imports; `python -m pytest` works from the repository root.
- Duplicate executable trees under `data/` archived outside the active runtime.
- Expanded, endpoint-allowlisted, read-only 3Commas bot normalisation.
- Production-versus-live configuration reconciliation output.
- Operating categories that keep production, live, research, validation and recommendations separate.
- Route manifest, UTF-8 cleanup, system-integrity output and stronger publication safety checks.
- V31.2.1 file manifest retained under `audit/`.

## Deliberately not included
- Bot starts/stops or settings changes.
- Order placement, deal closure or fund transfers.
- Automatic promotion of research settings.
- Deployment scoring or capital-allocation commands.
- Interface redesign.

The next planned build is V32.1.0: Canonical Operating State.
