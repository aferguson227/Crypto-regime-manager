# V68 Runtime State Separation V2 — Compile-Safe Packaging Fix

The previous package passed its test suite but failed `compileall` because
`scripts/installer_preflight.py` contained an import before `from __future__ import annotations`.

Fixes:
- restores legal module ordering: shebang → module docstring → future import → normal imports;
- adds a regression test for future-import placement;
- adds a package sanity check to the installer itself;
- the installer now extracts and compiles the exact embedded Current Source ZIP before stopping any CRM background service;
- if packaged source ever fails compilation again, installation aborts before touching the running CRM environment.

Runtime State Separation, Git-native source gating, atomic staging, rollback and always-restart fail-safe remain unchanged.
