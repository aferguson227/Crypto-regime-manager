# V40.0.0 — Unified Core Managers

V40 removes duplicated operational plumbing by introducing one authoritative manager for generated outputs, workflows, release validation, diagnostics and UI validation.

## Key reliability changes

- Build System 4.0 no longer calls `git restore` directly for generated outputs.
- Runtime generated files are restored only after Git confirms that they are tracked.
- Untracked files such as `docs/diagnostics_runtime.json` are skipped safely.
- Builds clean tracked runtime outputs before pre-flight and again after the build, reducing GitHub Desktop noise.
- Workflow, release, diagnostics and UI validation are coordinated through shared Python modules.
- Regression tests prevent blind generated-file restores from returning in later releases.

Trading remains read-only and all live bot or capital changes remain manual.
