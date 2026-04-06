from __future__ import annotations

from selenium.webdriver.common.by import By

from frontend.test_support import BASE_URL, FrontendBrowserTestCase


class PreviewLoginSmokeTests(FrontendBrowserTestCase):
    def test_preview_login_reaches_dashboard(self):
        self._log("Opening login preview page.")
        self.driver.get(f"{BASE_URL}/login/preview")

        self._log("Authenticating through preview login.")
        self._click_element(
            By.XPATH,
            "//article[contains(@class,'preview-user-card')][.//span[contains(@class,'preview-role') and normalize-space()='admin']]//button",
        )
        self._wait_for_post_login_navigation()

        self._assert_title("Dashboard")


if __name__ == "__main__":
    import unittest

    unittest.main()