from __future__ import annotations

import hashlib

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
        self.assertEqual(main.api_keys.find_one({"owner_id": ""}), None)

        seeded_key = main.api_keys.find_one({"course_id": 1})
        self.assertIsNotNone(seeded_key)
        self.assertTrue(isinstance(seeded_key.get("hash"), str) and len(seeded_key.get("hash")) == 64)
        self.assertEqual(seeded_key.get("owner_type"), "person")

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

    def test_regenerate_api_key_returns_plaintext_once_and_stores_hash(self):
        self._log("Regenerating a course API key. Expecting plaintext response and hash-only storage.")
        response = self.client.post(
            "/courses/1/api-key/regenerate",
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        plaintext_key = (payload or {}).get("api_key")
        self.assertTrue(isinstance(plaintext_key, str) and plaintext_key.startswith("sk_kent_"))
        self.assertNotIn("hash", payload or {})
        self.assertNotIn("u_id", payload or {})
        self.assertNotIn("created_by", payload or {})
        self.assertNotIn("c_id", payload or {})

        stored = main.api_keys.find_one({"course_id": 1, "owner_type": "person", "owner_id": "ksuid000000001", "key_name": "key-1"})
        self.assertIsNotNone(stored)
        self.assertEqual(stored.get("hash"), hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest())
        self.assertEqual(stored.get("owner_type"), "person")
        self.assertEqual(stored.get("owner_id"), "ksuid000000001")
        self.assertEqual(stored.get("course_id"), 1)
        self.assertNotIn("created_by", stored)

    def test_regenerate_group_api_key_tracks_group_and_creator(self):
        self._log("Regenerating a group-owned API key. Expecting group metadata and creator tracking.")
        response = self.client.post(
            "/courses/1/api-key/regenerate",
            json={
                "ownerType": "group",
                "groupId": "group-se3010-a",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json() or {}
        self.assertEqual(payload.get("owner_type"), "group")
        self.assertEqual(payload.get("group_created_by"), "ksuid000000001")

        stored = main.api_keys.find_one({"course_id": 1, "owner_type": "group", "owner_id": "group-se3010-a", "key_name": "key-1"})
        self.assertIsNotNone(stored)
        self.assertEqual(stored.get("owner_type"), "group")
        self.assertEqual(stored.get("owner_id"), "group-se3010-a")
        self.assertEqual(stored.get("group_created_by"), "ksuid000000001")

    def test_student_can_generate_own_key_once_then_hits_cooldown(self):
        self._log("Generating a self-service API key as a student and verifying the cooldown blocks a second request.")
        first_response = self.client.post(
            "/courses/1/api-key/regenerate",
            headers=self.student_headers,
        )
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            "/courses/1/api-key/regenerate",
            headers=self.student_headers,
        )
        self.assertEqual(second_response.status_code, 429)

        payload = second_response.get_json() or {}
        self.assertIn("wait", (payload.get("error") or "").lower())

    def test_api_key_cooldown_is_per_key_not_per_user(self):
        self._log("Generating a key as student and verifying same key owner/name cannot be overridden within cooldown window.")
        first_response = self.client.post(
            "/courses/1/api-key/regenerate",
            headers=self.student_headers,
        )
        self.assertEqual(first_response.status_code, 200)

        student_second = self.client.post(
            "/courses/1/api-key/regenerate",
            headers=self.student_headers,
        )
        self.assertEqual(student_second.status_code, 429)

        payload = student_second.get_json() or {}
        self.assertIn("wait", (payload.get("error") or "").lower())

    def test_courses_include_has_api_key_state(self):
        self._log("Fetching course list and checking has_api_key toggles with delete/regenerate operations.")
        before = self.client.get("/courses", headers=self.admin_headers)
        self.assertEqual(before.status_code, 200)
        before_payload = before.get_json()
        self.assertIsInstance(before_payload, list)
        course_before = next((course for course in before_payload if course.get("id") == 1), None)
        self.assertIsNotNone(course_before)
        self.assertEqual(course_before.get("has_api_key"), True)

        delete_response = self.client.delete("/courses/1/api-key", headers=self.admin_headers)
        self.assertEqual(delete_response.status_code, 200)

        after_delete = self.client.get("/courses", headers=self.admin_headers)
        after_delete_payload = after_delete.get_json()
        self.assertIsInstance(after_delete_payload, list)
        course_after_delete = next((course for course in after_delete_payload if course.get("id") == 1), None)
        self.assertIsNotNone(course_after_delete)
        self.assertEqual(course_after_delete.get("has_api_key"), False)

        regenerate_response = self.client.post("/courses/1/api-key/regenerate", headers=self.admin_headers)
        self.assertEqual(regenerate_response.status_code, 200)

        after_regenerate = self.client.get("/courses", headers=self.admin_headers)
        after_regenerate_payload = after_regenerate.get_json()
        self.assertIsInstance(after_regenerate_payload, list)
        course_after_regenerate = next((course for course in after_regenerate_payload if course.get("id") == 1), None)
        self.assertIsNotNone(course_after_regenerate)
        self.assertEqual(course_after_regenerate.get("has_api_key"), True)

    def test_instructor_cannot_update_instructor_member_key_limit(self):
        self._log("Instructor tries to change another instructor key limit. Expecting HTTP 403.")
        response = self.client.patch(
            "/courses/1/members/KSUID000000002/key-limit",
            json={"keyLimit": 3},
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_set_member_key_limit_above_course_limit(self):
        self._log("Admin attempts to set member key limit above course key limit. Expecting HTTP 400.")
        response = self.client.patch(
            "/courses/2/members/student.alt2@kent.edu/key-limit",
            json={"keyLimit": 3},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json() or {}
        self.assertIn("cannot exceed", payload.get("error", ""))

    def test_admin_can_update_instructor_handout_limit(self):
        self._log("Admin updates course instructor handout limit and value persists on the course.")
        response = self.client.patch(
            "/courses/1/instructor-handout-limit",
            json={"instructorHandoutLimit": 2},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json() or {}
        self.assertEqual(payload.get("instructor_handout_limit"), 2)

    def test_non_admin_cannot_update_instructor_handout_limit(self):
        self._log("Instructor attempts to update instructor handout limit. Expecting HTTP 403.")
        response = self.client.patch(
            "/courses/1/instructor-handout-limit",
            json={"instructorHandoutLimit": 4},
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_handout_generation_respects_handout_limit(self):
        self._log("Admin handouts respect course-wide max active handed-out keys.")

        set_limit_response = self.client.patch(
            "/courses/1/instructor-handout-limit",
            json={"instructorHandoutLimit": 2},
            headers=self.admin_headers,
        )
        self.assertEqual(set_limit_response.status_code, 200)

        first = self.client.post(
            "/courses/1/api-key/regenerate",
            json={"ownerType": "group", "groupId": "group-se3010-a", "keyName": "key-1", "slotIndex": 1},
            headers=self.admin_headers,
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            "/courses/1/api-key/regenerate",
            json={"ownerType": "person", "ownerId": "KSUID000000003", "keyName": "key-1", "slotIndex": 1},
            headers=self.admin_headers,
        )
        self.assertEqual(second.status_code, 200)

        third = self.client.post(
            "/courses/1/api-key/regenerate",
            json={"ownerType": "person", "ownerId": "KSUID000000004", "keyName": "key-1", "slotIndex": 1},
            headers=self.admin_headers,
        )
        self.assertEqual(third.status_code, 400)
        payload = third.get_json() or {}
        self.assertIn("Instructor handout key limit reached", payload.get("error", ""))


if __name__ == "__main__":
    import unittest

    unittest.main()
