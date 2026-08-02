#!/usr/bin/env python3
"""Compatibility entry point for the RSA key-generation utility."""

from tools.generate_3commas_rsa_keys import main


if __name__ == "__main__":
    raise SystemExit(main())