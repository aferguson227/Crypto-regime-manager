# V69 Incoming-Aware Semantic Preflight

The remaining genuine local change was `RUN_KUCOIN_LIVE_SERVICE.ps1`. Its six-line
runtime-application preparation block is not an unknown local customization: it exactly
matches the incoming V69 source.

The installer now distinguishes:
- line-ending-only noise -> ignored;
- genuine local content that exactly matches the incoming release -> preserved and allowed;
- genuine local content not represented by the incoming release -> still blocks installation.

This prevents a legitimate earlier hotfix, already incorporated into the new release,
from blocking its own upgrade while retaining strict protection for unrelated source edits.
