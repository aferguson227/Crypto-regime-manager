#!/usr/bin/env python3
"""Generate a 3Commas RSA key pair locally.

Outputs are written to a new local folder named threecommas_private_setup.
NEVER commit or upload that folder to GitHub.
"""
from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

OUT = Path("threecommas_private_setup")
OUT.mkdir(exist_ok=True)

private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)
public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
private_b64 = base64.b64encode(private_pem).decode("ascii")

(OUT / "public_key_3commas.pem").write_bytes(public_pem)
(OUT / "private_key_BACKUP.pem").write_bytes(private_pem)
(OUT / "github_secret_PRIVATE_KEY_B64.txt").write_text(private_b64, encoding="ascii")
(OUT / "README_PRIVATE.txt").write_text(
    "KEEP THIS FOLDER PRIVATE.\n"
    "public_key_3commas.pem: paste into 3Commas.\n"
    "github_secret_PRIVATE_KEY_B64.txt: store as GitHub secret THREECOMMAS_RSA_PRIVATE_KEY_B64.\n"
    "private_key_BACKUP.pem: offline backup; never upload it.\n",
    encoding="utf-8",
)
print(f"Created RSA setup files in: {OUT.resolve()}")
print("Never commit or upload this folder.")
