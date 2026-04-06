from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "rocky-interface"
BACKEND_DIR = ROOT / "rocky-backend"
BASE_URL = "http://127.0.0.1:4173"
NPM_BIN = "npm.cmd" if os.name == "nt" else "npm"
PYTHON_BIN = sys.executable


class FrontendBrowserTestCase(unittest.TestCase):
    @classmethod
    def _log(cls, message: str):
        print(f"[frontend-e2e] {message}", flush=True)

    @classmethod
    def setUpClass(cls):
        cls._log("Seeding and starting backend API for browser tests.")
        subprocess.run([PYTHON_BIN, "seed_from_backend.py"], cwd=BACKEND_DIR, check=True)

        backend_env = os.environ.copy()
        backend_env.update(
            {
                "ROCKY_APP_ENV": "testing",
                "ROCKY_DB_BACKEND": "mongita",
                "ROCKY_ENABLE_DB_INSPECTOR": "false",
            }
        )

        cls.backend = subprocess.Popen(
            [PYTHON_BIN, "main.py"],
            cwd=BACKEND_DIR,
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        cls._wait_for_backend()

        cls._log("Starting frontend dev server for browser tests.")
        env = os.environ.copy()
        env.update(
            {
                "PUBLIC_APP_ENV": "testing",
                "PUBLIC_API_BASE_URL": "http://127.0.0.1:5001",
                "PUBLIC_ENABLE_DBTEST": "false",
            }
        )

        cls.frontend = subprocess.Popen(
            [NPM_BIN, "run", "dev", "--", "--host", "127.0.0.1", "--port", "4173"],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        cls._wait_for_server()
        cls._log("Frontend dev server is reachable.")

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1600,1200")
        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 15)
        cls._log("Chrome WebDriver initialized.")

    @classmethod
    def tearDownClass(cls):
        cls._log("Cleaning up browser and dev server.")
        if hasattr(cls, "driver"):
            cls.driver.quit()
        if hasattr(cls, "frontend") and cls.frontend.poll() is None:
            cls.frontend.terminate()
            try:
                cls.frontend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.frontend.kill()

        if hasattr(cls, "backend") and cls.backend.poll() is None:
            cls.backend.terminate()
            try:
                cls.backend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.backend.kill()

    @classmethod
    def _wait_for_backend(cls):
        deadline = time.time() + 60
        while time.time() < deadline:
            if cls.backend.poll() is not None:
                raise RuntimeError("Backend server exited before tests started.")
            try:
                with urlopen("http://127.0.0.1:5001/health", timeout=2):
                    return
            except URLError:
                time.sleep(1)
        raise TimeoutError("Timed out waiting for backend server.")

    @classmethod
    def _wait_for_server(cls):
        deadline = time.time() + 60
        cls._log("Waiting for frontend server readiness.")
        while time.time() < deadline:
            if cls.frontend.poll() is not None:
                raise RuntimeError("Frontend dev server exited before tests started.")
            try:
                with urlopen(BASE_URL, timeout=2):
                    return
            except URLError:
                time.sleep(1)
        raise TimeoutError("Timed out waiting for frontend dev server.")

    def _assert_title(self, expected: str):
        def heading_matches(driver):
            try:
                return driver.find_element(By.CSS_SELECTOR, ".view-title h1").text.strip() == expected
            except (NoSuchElementException, StaleElementReferenceException):
                return False

        self.wait.until(heading_matches)

    def _wait_for_post_login_navigation(self):
        try:
            self.wait.until(EC.url_contains("/"))
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".view-title h1")))
        except TimeoutException as exc:
            self._log(f"Login navigation timeout. Current URL: {self.driver.current_url}")
            raise exc

    def _click_element(self, by: By, value: str, retries: int = 3):
        for attempt in range(retries):
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
                element.click()
                return
            except StaleElementReferenceException:
                if attempt == retries - 1:
                    raise