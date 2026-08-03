# 3Commas RSA setup — Starter plan

This release uses a self-generated RSA key and read-only `BOTS_READ` permission.

## Generate keys locally

On Windows, open PowerShell in the repository folder and run:

```powershell
py -m pip install cryptography>=43,<47
py scripts/generate_3commas_rsa_keys.py
```

This creates `threecommas_private_setup`. Never upload or commit this folder.

- Paste `public_key_3commas.pem` into the 3Commas self-generated API form.
- Store the API key returned by 3Commas as GitHub secret `THREECOMMAS_API_KEY`.
- Store the entire single-line content of `github_secret_PRIVATE_KEY_B64.txt` as GitHub secret `THREECOMMAS_RSA_PRIVATE_KEY_B64`.
- Keep `private_key_BACKUP.pem` offline as a recovery backup.

Grant only `BOTS_READ`. Disable the IP whitelist. The workflow validates authentication, reads DCA bots and active deals, then publishes sanitised data.
