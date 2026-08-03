CRYPTO REGIME MANAGER V22.0.0 EASY UPDATE

1. Extract this ZIP completely.
2. Put the extracted Crypto_Regime_Manager_V22_0_0_Easy_Update folder directly inside C:\Crypto\Projects.
3. Double-click INSTALL_V22_EASY.bat.
4. The installer backs up important state, copies the V22 files, normalises JSON files to UTF-8 without BOM, compiles the Python engine and runs the V19–V22 checks.
5. Review the changes in GitHub Desktop, commit, push, then run the normal Update Crypto Regime Manager workflow.

Preserved automatically or excluded from the update package:
- .git
- data
- backups
- private 3Commas/API credential folders
- docs/candidate_registry.json
- docs/health_history.json
- docs/strategies.json
- docs/threecommas.json

The existing config.json is backed up before the V22 configuration is installed.
V22 remains advisory and read-only. It cannot modify live bots, DCA settings, entries or exits.
