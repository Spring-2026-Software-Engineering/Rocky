from __future__ import annotations

from backend.test_support import BackendTestCase, main


class UserSettingsTests(BackendTestCase):
    def test_get_user_settings_returns_seeded_values(self):
        self._log("Requesting user settings for seeded users.")

        response = self.client.get(
            "/user-settings",
            query_string={"userId": "local-admin", "email": "admin.local@kent.edu"},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["settings"]["themePreference"], "light")
        self.assertEqual(payload["settings"]["widgets"][0]["title"], "Analytics")

    def test_patch_user_setting_updates_theme(self):
        self._log("Patching themePreference through key endpoint. Expecting persisted update.")
        update_response = self.client.patch(
            "/user-settings/themePreference",
            json={"userId": "local-admin", "email": "admin.local@kent.edu", "value": "dark"},
            headers=self.admin_headers,
        )
        self.assertEqual(update_response.status_code, 200)

        read_response = self.client.get(
            "/user-settings",
            query_string={"userId": "local-admin", "email": "admin.local@kent.edu"},
            headers=self.admin_headers,
        )
        self.assertEqual(read_response.status_code, 200)
        payload = read_response.get_json()
        self.assertEqual(payload["settings"]["themePreference"], "dark")

        stored_user = main.users.find_one({"email": "admin.local@kent.edu"})
        self.assertIsNotNone(stored_user)
        self.assertEqual((stored_user.get("settings") or {}).get("themePreference"), "dark")
        self.assertEqual((stored_user.get("settings") or {}).get("widgets"), ["analytics", "system-info"])

    def test_widgets_are_stored_per_user(self):
        self._log("Updating widgets through user settings patch and verifying per-user storage.")

        custom_widgets = [
            {"widgetId": "analytics"},
            {"widgetId": "notifications"},
        ]

        update_response = self.client.patch(
            "/user-settings",
            json={"userId": "local-admin", "email": "admin.local@kent.edu", "patch": {"widgets": custom_widgets}},
            headers=self.admin_headers,
        )
        self.assertEqual(update_response.status_code, 200)

        admin_widgets_response = self.client.get("/widgets/default", headers=self.admin_headers)
        self.assertEqual(admin_widgets_response.status_code, 200)
        admin_widgets = admin_widgets_response.get_json()
        self.assertEqual(admin_widgets[0]["title"], "Analytics")
        self.assertEqual(admin_widgets[1]["title"], "Notifications")
        self.assertEqual(admin_widgets[0]["widgetId"], "analytics")
        self.assertEqual(admin_widgets[0]["link"], "/widgets/default#analytics")

        student_widgets_response = self.client.get("/widgets/default", headers=self.student_headers)
        self.assertEqual(student_widgets_response.status_code, 200)
        student_widgets = student_widgets_response.get_json()
        self.assertIn("widgetId", student_widgets[0])
        self.assertIn("link", student_widgets[0])


if __name__ == "__main__":
    import unittest

    unittest.main()