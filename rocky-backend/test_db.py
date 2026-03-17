import unittest
from mongita import MongitaClientMemory
import main


class BaseTest(unittest.TestCase):
    def setUp(self):
        # Swap to in-memory DB so tests never touch disk data
        client = MongitaClientMemory()
        db = client["test_db"]
        main.users = db["users"]
        main.courses = db["courses"]
        main.api_keys = db["api_keys"]

        main.app.config["TESTING"] = True
        self.client = main.app.test_client()

class UserTests(BaseTest):
    def test_create_user(self):
        response = self.client.post("/users", json={
            "name": "Alice",
            "email": "alice@example.com",
            "flash_id": "alice123",
            "role": "student"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "User created")
        