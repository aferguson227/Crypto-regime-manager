# V68 Runtime State Separation 1.0

This hotfix addresses the repeated installer failures caused by live/generated JSON sharing the Git working tree with source code.

## New architecture

**Authoritative runtime state**
`C:\Crypto\CRM_Data\Runtime\State`

**Resident Live Data Service application**
`C:\Crypto\CRM_Data\Runtime\App`

**Git `docs/*.json`**
Controlled publication snapshots only. They are never treated as source files.

## Behaviour

- The resident KuCoin Live Data Service runs from the isolated Runtime App and no longer writes continuously into `C:\Crypto\Projects\docs`.
- Each live-service cycle imports the external authoritative state, performs its calculations, then captures the new state back to `CRM_Data\Runtime\State`.
- The Local Agent remains the controlled publication bridge. It aligns Git, imports external runtime state once, rebuilds dependent intelligence, captures the result externally, then publishes the snapshot.
- Research already runs in an isolated worker and remains separate.
- The installer treats every `docs/*.json` file as generated/publication state, never genuine source.
- Release commits stage source/static files only and do not traverse/stage publication JSON.
- The integrated preflight and fail-safe remain mandatory.
- Unknown changes to Python, PowerShell, HTML, JavaScript, CSS, config source, tests, etc. still stop installation safely.

This is the foundation intended for V69's event-driven Live Trading State Engine.
