# V69 Semantic Git Preflight Hotfix

Windows Git was reporting many historical source files as modified solely because
their working-tree LF/CRLF representation differed from Git's canonical content.
Only `RUN_KUCOIN_LIVE_SERVICE.ps1` had a real six-line content change in the
diagnostic supplied during the V69 install attempt.

This hotfix:
- classifies tracked modifications with an EOL-insensitive semantic diff;
- ignores only LF/CRLF-only working-tree noise;
- still blocks genuine content edits, untracked source, conflicts, additions,
  deletions, renames and staged semantic changes;
- keeps runtime/publication JSON outside the source gate;
- adds `.gitattributes` with canonical LF text policy so future checkouts stop
  recreating this false dirty-tree state;
- retains the V68/V69 compile-safe, runtime-separation, rollback and manifest
  staging safeguards.

The installer does not blindly restore the genuine live-service script change.
The incoming V69 source already contains the required live-service startup/runtime
preparation logic, and genuine semantic differences remain protected by preflight.
