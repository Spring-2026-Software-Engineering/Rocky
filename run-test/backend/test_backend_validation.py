import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "rocky-backend"
SEED_MODULE_PATH = BACKEND_PATH / "seed_from_local_api.py"
seed_spec = importlib.util.spec_from_file_location("seed_from_local_api", SEED_MODULE_PATH)
if seed_spec is None or seed_spec.loader is None:
    raise RuntimeError(f"Unable to load backend seed module from {SEED_MODULE_PATH}")
seed_backend = importlib.util.module_from_spec(seed_spec)
seed_spec.loader.exec_module(seed_backend)

main = seed_backend.main


class BackendValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_backend.use_in_memory_db()
        main.app.config["TESTING"] = True
        cls.client = main.app.test_client()

    def setUp(self):
        seed_backend.use_in_memory_db()
        main.user_settings.delete_many({})

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

    def test_create_user_accepts_local_api_shape(self):
        self._log("Posting local-api style user payload without flash_id. Expecting HTTP 200.")
        response = self.client.post(
            "/users",
            json={
                "_id": "acct-local-100",
                "name": "Local Api User",
                "email": "local.api.user@kent.edu",
                "role": "client",
            },
        )
        self.assertEqual(response.status_code, 200)
        saved = main.users.find_one({"email": "local.api.user@kent.edu"})
        self.assertIsNotNone(saved)
        self.assertEqual(saved.get("external_id"), "acct-local-100")
        self.assertTrue(saved.get("flash_id", "").startswith("seed-"))

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

    def test_create_course_accepts_local_api_shape(self):
        self._log("Posting local-api style course payload. Expecting HTTP 200 and normalized storage.")
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
                    {"accountEmail": "pnarayanan@kent.edu", "role": "instructor"},
                    {"accountEmail": "student.local@kent.edu", "role": "student"},
                ],
                "groups": [
                    {
                        "id": "group-cs4550-cloud",
                        "name": "Cloud Ops",
                        "memberEmails": ["student.local@kent.edu"],
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200)

        saved = main.courses.find_one({"id": 101})
        self.assertIsNotNone(saved)
        self.assertEqual(saved.get("semester"), "Summer 2027")
        self.assertEqual(saved.get("semester_obj", {}).get("term"), "summer")
        self.assertEqual(len(saved.get("members", [])), 2)
        self.assertEqual(len(saved.get("groups", [])), 1)

    def test_create_api_key_rejects_bad_payload(self):
        self._log("Posting invalid API key expiration payload. Expecting HTTP 400.")
        response = self.client.post(
            "/api_keys",
            json={"u_id": "good.user@kent.edu", "c_id": "course-1", "expire": "not-iso"},
        )
        self.assertEqual(response.status_code, 400)

    def test_get_user_settings_returns_default(self):
        self._log("Requesting user settings for unknown scope. Expecting default settings.")
        response = self.client.get(
            "/user-settings",
            query_string={"userId": "local-003", "email": "admin.local@kent.edu"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["settings"]["themePreference"], "system")

    def test_patch_user_setting_updates_theme(self):
        self._log("Patching themePreference through key endpoint. Expecting persisted update.")
        update_response = self.client.patch(
            "/user-settings/themePreference",
            json={"userId": "local-003", "email": "admin.local@kent.edu", "value": "dark"},
        )
        self.assertEqual(update_response.status_code, 200)

        read_response = self.client.get(
            "/user-settings",
            query_string={"userId": "local-003", "email": "admin.local@kent.edu"},
        )
        self.assertEqual(read_response.status_code, 200)
        payload = read_response.get_json()
        self.assertEqual(payload["settings"]["themePreference"], "dark")

    def test_analytics_and_widget_endpoints_exist(self):
        self._log("Verifying analytics/widgets endpoints are available for remote frontend mode.")

        endpoints = [
            "/analytics/kpis",
            "/analytics/activity",
            "/widgets/default",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, msg=f"Expected 200 for {endpoint}")
            payload = response.get_json()
            self.assertIsInstance(payload, list, msg=f"Expected list payload for {endpoint}")
            self.assertGreater(len(payload), 0, msg=f"Expected non-empty payload for {endpoint}")


if __name__ == "__main__":
    unittest.main()
