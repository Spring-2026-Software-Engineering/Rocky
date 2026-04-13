from __future__ import annotations

import unittest

from backend.course_actions import create_course_group, regenerate_course_api_key


class FakeCollection:
    def __init__(self):
        self.rows: list[dict] = []

    def find_one(self, query: dict):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()):
                return row
        return None

    def insert_one(self, doc: dict):
        self.rows.append(dict(doc))

    def replace_one(self, query: dict, doc: dict):
        for idx, row in enumerate(self.rows):
            if all(row.get(k) == v for k, v in query.items()):
                self.rows[idx] = dict(doc)
                return


class CourseActionsUnitTests(unittest.TestCase):
    def test_create_course_group_generates_unique_id(self):
        course = {
            "groups": [
                {"id": "team-a-1", "name": "Team A", "memberIds": [], "key_limit": 1}
            ]
        }

        updated = create_course_group(course, "Team A")

        new_group = updated["groups"][-1]
        self.assertEqual(new_group["id"], "team-a-2")
        self.assertEqual(new_group["name"], "Team A")

    def test_regenerate_course_api_key_upserts_same_owner_key(self):
        collection = FakeCollection()
        course = {"id": 1, "code": "SE 3010"}

        first = regenerate_course_api_key(course, collection, "ksuid000000001")
        second = regenerate_course_api_key(course, collection, "ksuid000000001")

        self.assertEqual(len(collection.rows), 1)
        self.assertEqual(first["owner_id"], "ksuid000000001")
        self.assertEqual(second["owner_id"], "ksuid000000001")
        self.assertNotEqual(first["api_key"], second["api_key"])


if __name__ == "__main__":
    unittest.main()
