# V68 Installer Manifest Staging Fix

Final Git staging now uses an explicit list of files that actually exist. Optional
documentation extensions with zero matches are skipped automatically. Runtime/publication
`docs/*.json` remains excluded. Only genuine transient Git indexing/read failures are retried.
This staging model is included for future installers.
