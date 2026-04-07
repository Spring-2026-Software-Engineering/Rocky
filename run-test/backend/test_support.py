from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "rocky-backend"
SEED_MODULE_PATH = BACKEND_PATH / "seed_from_backend.py"

seed_spec = importlib.util.spec_from_file_location("seed_from_backend", SEED_MODULE_PATH)
if seed_spec is None or seed_spec.loader is None:
    raise RuntimeError(f"Unable to load backend seed module from {SEED_MODULE_PATH}")

original_backend_package = sys.modules.get("backend")
temporary_backend_package = types.ModuleType("backend")
temporary_backend_package.__path__ = [str(BACKEND_PATH / "backend")]
sys.modules["backend"] = temporary_backend_package
try:
    seed_backend = importlib.util.module_from_spec(seed_spec)
    seed_spec.loader.exec_module(seed_backend)
finally:
    if original_backend_package is not None:
        sys.modules["backend"] = original_backend_package
    else:
        sys.modules.pop("backend", None)

main = seed_backend.main


class BackendTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_backend.use_in_memory_db()
        main.app.config["TESTING"] = True
        cls.client = main.app.test_client()

    def setUp(self):
        seed_backend.seed_from_backend()
        self.admin_headers = {
            "X-Rocky-User-Email": "admin.local@kent.edu",
            "X-Rocky-User-Is-Admin": "true",
        }
        self.student_headers = {
            "X-Rocky-User-Email": "student.local@kent.edu",
            "X-Rocky-User-Is-Admin": "false",
        }
        self.instructor_headers = {
            "X-Rocky-User-Email": "instructor.local@kent.edu",
            "X-Rocky-User-Is-Admin": "false",
        }

    def _log(self, message: str):
        print(f"[backend-test] {message}", flush=True)