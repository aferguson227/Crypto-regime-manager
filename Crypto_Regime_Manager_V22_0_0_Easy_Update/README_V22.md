# Crypto Regime Manager V22

V22 is the Decision Intelligence release. It preserves the V21 research engine and production guardrails while replacing the Research Queue with a coherent, mobile-first review workflow.

## Verification

1. Open `docs/index.html` and confirm the version badge shows V22.0.0.
2. Open `docs/research_queue.html` and confirm the page remains dark throughout.
3. Confirm each queued asset displays a priority, weakness score, evidence confidence, lifecycle stage and next manual action.
4. Expand **Compare all experiments** and verify alternatives remain advisory.
5. Confirm the safeguards section states that automatic production changes are disabled.
6. Run `python -m pytest` from the project root.
