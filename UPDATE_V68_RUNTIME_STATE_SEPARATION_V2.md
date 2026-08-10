# V68 Runtime State Separation 1.1 — Git-native source gate

The first Runtime State Separation installer still parsed `git status` output in Python.
On the user's Windows repository, some `docs/*.json` publication files were consequently
reported as source/unclassified even though the architecture explicitly classifies all
docs JSON as runtime/publication state.

V2 removes that fragile dependency.

Installer source cleanliness is now checked by Git itself:

`git status --porcelain -- . :(exclude,glob)docs/**/*.json`

Therefore:
- no `docs/*.json` file can block installation as a source change;
- docs JSON may remain dirty during an upgrade without contaminating the release;
- release staging still excludes all docs JSON;
- genuine Python/PowerShell/config/HTML/JS/CSS/test/source changes still block safely;
- the runtime-state separation architecture and atomic commit/fail-safe remain enabled.

This Git-native source gate is the standard for V69+ installers.
