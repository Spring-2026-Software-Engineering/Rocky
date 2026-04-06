from selenium.webdriver.common.by import By
from frontend.test_support import BASE_URL, FrontendBrowserTestCase


class ViewTitleE2ETests(FrontendBrowserTestCase):
    def test_each_view_displays_expected_title(self):
        self._log("Opening login preview page.")
        self.driver.get(f"{BASE_URL}/login/preview")

        self._log("Authenticating through preview login.")
        self._click_element(
            By.XPATH,
            "//article[contains(@class,'preview-user-card')][.//span[contains(@class,'preview-role') and normalize-space()='admin']]//button",
        )
        self._wait_for_post_login_navigation()

        self._assert_title("Dashboard")
        self._log("Verified default dashboard title after login.")

        view_expectations = [
            ("Users", "Users"),
            ("Courses", "Courses"),
            ("Analytics", "Analytics"),
            ("Account", "Account Settings"),
            ("Help", "Help Center"),
            ("Dashboard", "Dashboard"),
        ]

        for nav_text, expected_title in view_expectations:
            self._log(f"Navigating to view: {nav_text}")
            self._click_element(By.XPATH, f"//nav[contains(@class,'sidebar')]//button[normalize-space()='{nav_text}']")

            if nav_text == "Courses":
                self._log("Selecting first course from Courses popout.")
                self._click_element(By.CSS_SELECTOR, ".course-popout-item")

            self._assert_title(expected_title)
            self._log(f"Verified view title: {expected_title}")


if __name__ == "__main__":
    import unittest

    unittest.main()


if __name__ == "__main__":
    unittest.main()
