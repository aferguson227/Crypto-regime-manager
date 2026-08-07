# Crypto Regime Manager V17.0.1

Combined operator-efficiency production branch. See `README_V17.md` for the release overview.

Trading logic, DCA settings and forward-validation behaviour are preserved from V16.

## V33 Trading Command Centre

Open `docs/command_centre.html` for the unified read-only command view backed by `docs/command_state.json`.


## V38 Engineering Mode
Open `engineering.html` for engineering health and run `GENERATE_ENGINEERING_PACKAGE.cmd` to produce one evidence ZIP for future development.


### V40 reliability architecture
V40 uses shared core managers so builds, installers, diagnostics and engineering tools follow the same cleanup and validation policies.

### V41 unified decision workspace
V41 makes the Dashboard the canonical daily operating surface. It combines the current trading recommendation, capital and portfolio context, DCA settings, market state, 3Commas health, workflow/synchronisation health, active issues and interface quality on one consistent page. Legacy specialist pages remain available as drill-down evidence but no longer own navigation or release identity.
