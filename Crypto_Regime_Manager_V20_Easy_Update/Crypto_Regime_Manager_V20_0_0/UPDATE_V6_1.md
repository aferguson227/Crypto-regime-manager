# Updating to V6.1

1. In GitHub Desktop, **Fetch origin** and **Pull origin** if offered.
2. Keep the existing `data/`, `threecommas_private_setup/`, and `.git/` folders unchanged.
3. Copy everything from this package into the repository root and replace matching files.
4. Do not create or replace the `data/` folder; this package intentionally does not contain one.
5. Commit with `Refactor to modular core V6.1` and push.
6. Run **Update Crypto Regime Manager**, then **Update 3Commas Deal Dashboard**.
7. Confirm the website shows V6.1 and both workflows have green ticks.

The old script paths remain valid through compatibility wrappers, so the workflows and existing secrets continue to work.
