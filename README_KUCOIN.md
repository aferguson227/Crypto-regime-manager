# KuCoin direct read-only capital source

V41.1 can read spot account balances directly from KuCoin so deployable capital no longer depends on the 3Commas Starter-plan account-balance quota.

Create a **separate KuCoin API key with General/read-only permission only**. Do not enable Spot trading, transfers or withdrawals for this key.

Add these GitHub Actions repository secrets:

- `KUCOIN_API_KEY`
- `KUCOIN_API_SECRET`
- `KUCOIN_API_PASSPHRASE`
- optional `KUCOIN_API_KEY_VERSION` (defaults to `2`; set this to the version shown for your KuCoin API key if different)
- optional `KUCOIN_API_BASE_URL` (defaults to `https://api.kucoin.com`)

After the next CRM Data Refresh, `docs/kucoin_account.json` should report `status: ok`, and Capital Intelligence will prefer KuCoin free USDT over 3Commas account-balance data.

V41.1 remains read-only. Future execution integrations are present only as disabled provider definitions.


## Connectivity hotfix
Private requests now include Content-Type, use safe key-version and official-region fallback, publish sanitised diagnostics, and never abort the whole CRM refresh solely because this optional capital source is degraded.
