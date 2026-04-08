from __future__ import annotations

import hashlib
import secrets

API_KEY_PREFIX = "sk_kent_"


def generate_api_key_pair() -> tuple[str, str]:
    """Return (plaintext_key, sha256_hash)."""
    plaintext_key = f"{API_KEY_PREFIX}{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()
    return plaintext_key, key_hash
