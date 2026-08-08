# Crypto Regime Manager V45.0.0 — Capital Truth & Local Autonomous Agent

V41.2 corrects capital semantics, bot lifecycle state and DCA field mapping, and moves private KuCoin collection from U.S.-routed GitHub-hosted runners to a local Windows agent.

## Key changes
- SO deviation uses one canonical alias chain.
- Active deals, enabled-idle bots and disabled bots are distinct states.
- Portfolio reserved capital protects active-deal DCA ladders only; theoretical idle-bot exposure is shown separately.
- GitHub Data Refresh no longer calls the private KuCoin API.
- Local Agent collects KuCoin through the user's own network and publishes validated material changes.
- Local credentials are protected with Windows DPAPI and stored outside the repository.
- Legacy repository backup folders remain excluded; future operational backups belong outside the source tree.
- Kraken research evidence remains a deployment gate; automatic candidate promotion is not enabled yet.
