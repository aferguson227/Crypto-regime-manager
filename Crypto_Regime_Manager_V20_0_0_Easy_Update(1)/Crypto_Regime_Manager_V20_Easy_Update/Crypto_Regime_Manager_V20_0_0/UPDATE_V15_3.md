# V15.3 — Independent Forward-Evidence Boundary Fix

This release prevents historical SUI diagnostic data from being presented as SUI-T1 post-freeze validation.

## Changes

- Candidate forward age and sample size are calculated only from candles at or after the immutable `forward_test_start`.
- The dashboard reads SUI-T1 evidence from `forward_validation`, not the older Candidate A research summary.
- Historical diagnostic evidence and independent post-freeze evidence are labelled separately.
- The dashboard shows post-freeze days, candles, candidate deals, completed 30-day windows and profitable windows.
- A boundary-integrity warning is generated if a reported forward candle predates the candidate start.
- Existing production strategies, DCA settings and live execution permissions are unchanged.
