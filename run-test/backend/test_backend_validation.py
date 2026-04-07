from __future__ import annotations

from backend.test_support import BackendTestCase, main, seed_backend


class BackendValidationTests(BackendTestCase):

    def test_seed_database_rejects_invalid_records(self):
        self._log("Seeding in-memory database with mixed valid/invalid fixture data.")
        summary = seed_backend.seed_backend_from_fixture()
        self._log(f"Seed summary: {summary}")

        self.assertEqual(summary["users_inserted"], 2)
        self.assertEqual(summary["users_rejected"], 2)
        self.assertEqual(summary["courses_inserted"], 1)
        self.assertEqual(summary["courses_rejected"], 2)
        self.assertEqual(summary["api_keys_inserted"], 1)
        self.assertEqual(summary["api_keys_rejected"], 2)

        self.assertEqual(main.users.count_documents({}), 2)
        self.assertEqual(main.courses.count_documents({}), 1)
        self.assertEqual(main.api_keys.count_documents({}), 1)

        self.assertEqual(main.users.find_one({"email": "bad.role@kent.edu"}), None)
        self.assertEqual(main.courses.find_one({"name": "Invalid Course Term"}), None)
        self.assertEqual(main.api_keys.find_one({"u_id": ""}), None)

    def test_create_user_rejects_bad_payload(self):
        self._log("Posting invalid user payload. Expecting HTTP 400.")
        response = self.client.post(
            "/users",
            json={"first_name": "X", "last_name": "User", "email": "not-an-email", "id": "x1", "is_admin": False},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_accepts_valid_payload(self):
        self._log("Posting valid user payload. Expecting HTTP 200.")
        response = self.client.post(
            "/users",
            json={
                "first_name": "Good",
                "last_name": "User",
                "email": "good.user@kent.edu",
                "id": "KSUID000000100",
                "is_admin": False,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)

    def test_create_user_accepts_local_api_shape(self):
        self._log("Posting backend-style user payload without id. Expecting HTTP 200.")
        response = self.client.post(
            "/users",
            json={
                "first_name": "Local",
                "last_name": "Api User",
                "email": "local.api.user@kent.edu",
                "is_admin": False,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        saved = main.users.find_one({"email": "local.api.user@kent.edu"})
        self.assertIsNotNone(saved)
        self.assertTrue(saved.get("id", "").startswith("seed-"))

    def test_update_user_only_accepts_is_active_boolean(self):
        self._log("Updating user status through /users/<id>. Expecting boolean-only is_active support.")

        seeded_admin = main.users.find_one({"email": "admin.local@kent.edu"})
        self.assertIsNotNone(seeded_admin)
        user_id = seeded_admin.get("id")
        self.assertTrue(isinstance(user_id, str) and user_id)

        invalid_payload_response = self.client.put(
            f"/users/{user_id}",
            json={"first_name": "Nope"},
            headers=self.admin_headers,
        )
        self.assertEqual(invalid_payload_response.status_code, 400)

        invalid_type_response = self.client.put(
            f"/users/{user_id}",
            json={"is_active": "false"},
            headers=self.admin_headers,
        )
        self.assertEqual(invalid_type_response.status_code, 400)

        valid_response = self.client.put(
            f"/users/{user_id}",
            json={"is_active": False},
            headers=self.admin_headers,
        )
        self.assertEqual(valid_response.status_code, 200)

        updated = main.users.find_one({"id": user_id})
        self.assertIsNotNone(updated)
        self.assertEqual(updated.get("is_active"), False)

    def test_create_course_rejects_bad_payload(self):
        self._log("Posting invalid course term payload. Expecting HTTP 400.")
        response = self.client.post(
            "/courses",
            json={
                "name": "Broken",
                "instructor_ids": ["KSUID000000100"],
                "student_ids": ["KSUID000000100"],
                "semester": {"year": 2026, "term": "autumn"},
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_create_course_accepts_local_api_shape(self):
        self._log("Posting backend-style course payload. Expecting HTTP 201 and normalized storage.")
        response = self.client.post(
            "/courses",
            json={
                "id": 101,
                "code": "CS 4550",
                "name": "Cloud Computing",
                "instructor": "Dr. Priya Narayanan",
                "semester": "Summer 2027",
                "color": "#1d4ed8",
                "announcements": ["Welcome to Cloud Computing"],
                "members": [
                    {"id": "KSUID000000002", "role": "instructor"},
                    {"id": "KSUID000000003", "role": "student"},
                ],
                "groups": [
                    {
                        "id": "group-cs4550-cloud",
                        "name": "Cloud Ops",
                        "memberIds": ["KSUID000000003"],
                    }
                ],
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)

        saved = main.courses.find_one({"id": 101})
        self.assertIsNotNone(saved)
        self.assertEqual(saved.get("semester"), "Summer 2027")
        self.assertEqual(saved.get("semester_obj", {}).get("term"), "summer")
        self.assertEqual(len(saved.get("members", [])), 2)
        self.assertEqual(len(saved.get("groups", [])), 1)

    def test_legacy_api_key_endpoint_removed(self):
        self._log("Posting to removed legacy /api_keys endpoint. Expecting HTTP 404.")
        response = self.client.post(
            "/api_keys",
            json={"u_id": "good.user@kent.edu", "c_id": "course-1", "expire": "not-iso"},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    import unittest

    unittest.main()
