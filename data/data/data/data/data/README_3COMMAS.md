# Read-only 3Commas dashboard — V5.2.1

This add-on uses a separate 3Commas Developer API token with **BOTS_READ only**. It does not use or replace the KuCoin API key already connected inside 3Commas.

## Security model

- The API key and secret are stored only as encrypted GitHub Actions secrets.
- The browser never receives the credentials.
- The script does not call any write endpoint.
- Bot IDs, deal IDs, account IDs and raw API responses are not published.
- Default `publish_mode` is `masked`, which hides exact prices and dollar amounts because a public GitHub Pages site can be viewed by anyone who has the URL.

Change `threecommas.publish_mode` in `config.json` to `full` only if you explicitly accept publishing exact active-deal values on your public site.
