# V69 GitHub Publication Version Sync Fix

Runtime State Separation excluded all docs JSON from release commits. That was too broad:
GitHub Actions validates a small set of version-critical publication snapshots against
the application VERSION, so committed V67 snapshots caused V68/V69 refresh validation to fail.

The release now has an explicit 11-file release-identity snapshot allowlist. These files
are regenerated, preserved across the final atomic cleanup, and staged with the release.
All other runtime/publication JSON remains excluded from Git staging and authoritative
runtime state remains external under CRM_Data\Runtime\State.
