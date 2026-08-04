CRYPTO REGIME MANAGER V24.1.0 EASY UPDATE

1. Extract the ZIP.
2. Move the extracted V24 folder directly inside C:\Crypto\Projects (or your project root).
3. Double-click INSTALL_V24_EASY.bat.
4. Confirm the installer reports that all tests passed.
5. Commit and push the changes.
6. Run the normal update workflow.

V24 adds automatic research-only Coin Discovery, bounded 4-hour market screening and advisory DCA proposals.
It cannot add coins to production, alter 3Commas bots or apply DCA settings automatically.

After installation, run a discovery scan from the project folder:

python scripts\coin_discovery.py
