from __future__ import annotations

import importlib
import unittest


TEST_MODULES = [
    "backend.test_seed_data_shape",
    "backend.test_backend_validation",
    "backend.test_user_settings",
    "backend.test_course_api_history",
    "frontend.test_preview_login_chromedriver",
    "frontend.test_view_titles_chromedriver",
]


def load_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in TEST_MODULES:
        module = importlib.import_module(module_name)
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(load_suite())
    raise SystemExit(0 if result.wasSuccessful() else 1)