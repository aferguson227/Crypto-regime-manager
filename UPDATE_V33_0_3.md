# V33.0.3 — Account Intelligence

Adds read-only per-account detail and balance-table retrieval using ACCOUNTS_READ, account/balance completeness diagnostics, canonical account intelligence, and automatic downstream capital/command-state regeneration after every 3Commas refresh. The HTTP POST used for `account_table_data` is a documented read-only query and is restricted to that exact endpoint pattern. No trading, account mutation, order, deal-close or transfer capability is introduced.
