# CRM Build System 2.1

The build system makes testing the source repository a mandatory gate before a release ZIP can be created.

## One-click commands

- `BUILD_CRM.cmd` runs tests, publication validation, compilation, diagnostics, browser captures and creates a machine-readable build report.
- `CREATE_RELEASE.cmd` repeats the full build gate and creates a release ZIP plus SHA-256 manifest under `release/`.
- `RUN_DIAGNOSTICS.cmd` creates the redacted diagnostics ZIP used for remote review.

## PowerShell commands

```powershell
.\build.ps1 -Screenshots
.\test.ps1
.\package.ps1
.\release.ps1 -Tag -Push
```

A failed check returns a non-zero exit code and prevents packaging. Logs and build reports are written to `diagnostics_logs/`; review bundles are written to `diagnostics_exports/`.

The build and diagnostic tools are observational. They do not start or stop bots, modify 3Commas settings, close deals, submit orders or transfer funds.

## V2.0

Build System 2.1 validates canonical release metadata, restores generated acceptance artefacts, keeps application and build outcomes distinct, and preserves strict read-only safeguards.


## Build System 4.0
V40 centralises generated-output, workflow, release, diagnostics and UI validation in shared Python managers. Build scripts no longer perform direct generated-file `git restore` operations.
