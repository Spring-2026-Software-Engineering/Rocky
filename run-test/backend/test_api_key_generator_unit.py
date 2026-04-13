from __future__ import annotations

import importlib.util
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "rocky-backend" / "backend" / "api_key_generator.py"

spec = importlib.util.spec_from_file_location("api_key_generator", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load api_key_generator from {MODULE_PATH}")

api_key_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_key_module)

API_KEY_PREFIX = api_key_module.API_KEY_PREFIX
generate_api_key_pair = api_key_module.generate_api_key_pair


class ApiKeyGeneratorUnitTests(unittest.TestCase):
    def test_generate_api_key_pair_returns_prefixed_plaintext_and_hash(self):
        plaintext, key_hash = generate_api_key_pair()

        self.assertTrue(plaintext.startswith(API_KEY_PREFIX))
        self.assertEqual(len(key_hash), 64)
        self.assertEqual(key_hash, hashlib.sha256(plaintext.encode("utf-8")).hexdigest())

    def test_generate_api_key_pair_is_unique(self):
        first_plaintext, first_hash = generate_api_key_pair()
        second_plaintext, second_hash = generate_api_key_pair()

        self.assertNotEqual(first_plaintext, second_plaintext)
        self.assertNotEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()
