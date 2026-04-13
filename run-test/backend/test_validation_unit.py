from __future__ import annotations

import unittest

from backend.validation import parse_semester, validate_user_payload


class ValidationUnitTests(unittest.TestCase):
    def test_parse_semester_accepts_string_and_object(self):
        string_value, string_error = parse_semester("Fall 2026")
        object_value, object_error = parse_semester({"year": 2026, "term": "fall"})

        self.assertIsNone(string_error)
        self.assertEqual(string_value["year"], 2026)
        self.assertEqual(string_value["term"], "fall")

        self.assertIsNone(object_error)
        self.assertEqual(object_value["display"], "Fall 2026")

    def test_validate_user_payload_rejects_non_boolean_admin(self):
        cleaned, error = validate_user_payload(
            {
                "first_name": "Unit",
                "last_name": "Tester",
                "email": "unit.tester@kent.edu",
                "id": "KSUID000000999",
                "is_admin": "yes",
            }
        )

        self.assertIsNone(cleaned)
        self.assertEqual(error, "is_admin must be a boolean.")


if __name__ == "__main__":
    unittest.main()
