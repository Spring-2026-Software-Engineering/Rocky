import unittest

import seed_backend

main = seed_backend.main


class BackendValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_backend.use_in_memory_db()
        main.app.config["TESTING"] = True
        cls.client = main.app.test_client()

    def setUp(self):
        seed_backend.use_in_memory_db()

    def _log(self, message: str):
        print(f"[backend-test] {message}", flush=True)

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
            json={"name": "X", "email": "not-an-email", "flash_id": "x1", "role": "student"},
        )
        self.assertEqual(response.status_code, 400)

    def test_create_user_accepts_valid_payload(self):
        self._log("Posting valid user payload. Expecting HTTP 200.")
        response = self.client.post(
            "/users",
            json={
                "name": "Good User",
                "email": "good.user@kent.edu",
                "flash_id": "good100",
                "role": "student",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_create_course_rejects_bad_payload(self):
        self._log("Posting invalid course term payload. Expecting HTTP 400.")
        response = self.client.post(
            "/courses",
            json={
                "name": "Broken",
                "instructor_ids": ["good.user@kent.edu"],
                "student_ids": ["good.user@kent.edu"],
                "semester": {"year": 2026, "term": "autumn"},
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_create_api_key_rejects_bad_payload(self):
        self._log("Posting invalid API key expiration payload. Expecting HTTP 400.")
        response = self.client.post(
            "/api_keys",
            json={"u_id": "good.user@kent.edu", "c_id": "course-1", "expire": "not-iso"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
