from __future__ import annotations

from backend.test_support import BackendTestCase, seed_backend


class CourseApiHistoryTests(BackendTestCase):
    def test_api_history_tracks_group_membership(self):
        self._log("Recording API history for grouped and ungrouped users.")

        grouped_response = self.client.post(
            "/courses/1/api-history",
            json={"eventType": "request", "meta": {"path": "/v1/ask"}},
            headers=self.student_headers,
        )
        self.assertEqual(grouped_response.status_code, 201)
        grouped_payload = grouped_response.get_json()
        self.assertEqual(grouped_payload["is_group_member"], True)

        ungrouped_response = self.client.post(
            "/courses/3/api-history",
            json={"eventType": "request", "meta": {"path": "/v1/ask"}},
            headers=self.admin_headers,
        )
        self.assertEqual(ungrouped_response.status_code, 201)
        ungrouped_payload = ungrouped_response.get_json()
        self.assertEqual(ungrouped_payload["is_group_member"], False)

    def test_course_api_history_can_be_read_back(self):
        self._log("Reading seeded API history for course 1.")
        seed_backend.seed_from_backend()

        response = self.client.get("/courses/1/api-history", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload), 1)
        self.assertTrue(any(entry.get("group_id") for entry in payload))

    def test_analytics_and_widget_endpoints_exist(self):
        self._log("Verifying analytics/widgets endpoints are available for remote frontend mode.")

        endpoints = [
            "/analytics/kpis",
            "/analytics/activity",
            "/widgets/default",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint, headers=self.admin_headers)
            self.assertEqual(response.status_code, 200, msg=f"Expected 200 for {endpoint}")
            payload = response.get_json()
            self.assertIsInstance(payload, list, msg=f"Expected list payload for {endpoint}")
            self.assertGreater(len(payload), 0, msg=f"Expected non-empty payload for {endpoint}")


if __name__ == "__main__":
    import unittest

    unittest.main()