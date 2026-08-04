# Crypto Regime Manager V28.0.0

## Included
- Rebuilt Cloud Refresh page using the shared dark mobile shell.
- Removed cloud-status and dashboard-control overlap on Discovery and validation pages.
- Added an immutable Candidate Validation Queue for discovered coins and advisory DCA proposals.
- Added explicit fee-aware replay, walk-forward, risk-review and manual-approval gates.
- Added cloud publication of `candidate_validation.json` every scheduled cycle.
- Existing safeguards remain unchanged: no automatic bot, deal, DCA or production changes.

## Installation
Extract the ZIP directly inside the existing project folder and run `INSTALL_V28_EASY.bat`. Commit and push the installed files, then run the **V28 Autonomous Crypto Regime Refresh** workflow once.
