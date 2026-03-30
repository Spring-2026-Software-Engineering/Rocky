import re
from typing import Any

from flask import Flask
from flask import request, jsonify
from mongita import MongitaClientDisk
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = MongitaClientDisk()
db = client["rocky_db"]
users = db["users"]
courses = db["courses"]
api_keys = db["api_keys"]

ALLOWED_USER_ROLES = {"student", "instructor", "admin", "client"}
ALLOWED_TERMS = {"spring", "summer", "fall", "winter"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _parse_object_id(value: str):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _bad_request(message: str):
    return jsonify({"error": message}), 400


def validate_user_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    name = _normalize_str(payload.get("name"))
    email = _normalize_str(payload.get("email")).lower()
    flash_id = _normalize_str(payload.get("flash_id"))
    role = _normalize_str(payload.get("role")).lower()

    if not name:
        return None, "User name is required."
    if not email or not EMAIL_RE.match(email):
        return None, "A valid user email is required."
    if not flash_id:
        return None, "flash_id is required."
    if role not in ALLOWED_USER_ROLES:
        allowed_roles = ", ".join(sorted(ALLOWED_USER_ROLES))
        return None, f"Invalid role. Allowed values: {allowed_roles}."

    return {
        "name": name,
        "email": email,
        "flash_id": flash_id,
        "role": role,
    }, None


def validate_course_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    name = _normalize_str(payload.get("name"))
    instructor_ids = payload.get("instructor_ids")
    student_ids = payload.get("student_ids")
    semester = payload.get("semester")

    if not name:
        return None, "Course name is required."
    if not isinstance(instructor_ids, list) or not all(isinstance(v, str) and v.strip() for v in instructor_ids):
        return None, "instructor_ids must be a list of non-empty strings."
    if not isinstance(student_ids, list) or not all(isinstance(v, str) and v.strip() for v in student_ids):
        return None, "student_ids must be a list of non-empty strings."
    if not isinstance(semester, dict):
        return None, "semester must be an object containing year and term."

    year = semester.get("year")
    term = _normalize_str(semester.get("term")).lower()
    if not isinstance(year, int) or year < 2000 or year > 2100:
        return None, "semester.year must be an integer between 2000 and 2100."
    if term not in ALLOWED_TERMS:
        allowed_terms = ", ".join(sorted(ALLOWED_TERMS))
        return None, f"semester.term must be one of: {allowed_terms}."

    return {
        "name": name,
        "instructor_ids": [v.strip() for v in instructor_ids],
        "student_ids": [v.strip() for v in student_ids],
        "semester": {"year": year, "term": term},
    }, None


def validate_api_key_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    u_id = payload.get("u_id")
    c_id = payload.get("c_id")
    expire = payload.get("expire")

    if not isinstance(u_id, str) or not u_id.strip():
        return None, "u_id is required and must be a non-empty string."
    if not isinstance(c_id, str) or not c_id.strip():
        return None, "c_id is required and must be a non-empty string."
    if expire is not None:
        if not isinstance(expire, str):
            return None, "expire must be an ISO datetime string or null."
        try:
            datetime.fromisoformat(expire.replace("Z", "+00:00"))
        except ValueError:
            return None, "expire must be a valid ISO datetime string."

    return {
        "u_id": u_id.strip(),
        "c_id": c_id.strip(),
        "expire": expire,
    }, None


def seed_database(payload: dict[str, Any]) -> dict[str, int]:
    summary = {
        "users_inserted": 0,
        "users_rejected": 0,
        "courses_inserted": 0,
        "courses_rejected": 0,
        "api_keys_inserted": 0,
        "api_keys_rejected": 0,
    }

    users.delete_many({})
    courses.delete_many({})
    api_keys.delete_many({})

    for item in payload.get("users", []):
        cleaned, error = validate_user_payload(item)
        if error:
            summary["users_rejected"] += 1
            continue
        cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
        users.insert_one(cleaned)
        summary["users_inserted"] += 1

    for item in payload.get("courses", []):
        cleaned, error = validate_course_payload(item)
        if error:
            summary["courses_rejected"] += 1
            continue
        courses.insert_one(cleaned)
        summary["courses_inserted"] += 1

    for item in payload.get("api_keys", []):
        cleaned, error = validate_api_key_payload(item)
        if error:
            summary["api_keys_rejected"] += 1
            continue
        cleaned["created"] = datetime.now(timezone.utc).isoformat()
        api_keys.insert_one(cleaned)
        summary["api_keys_inserted"] += 1

    return summary


# ── Users ──────────────────────────────────────────────────────────────────────

@app.route("/users", methods=["POST"])
def create_user():
    cleaned, error = validate_user_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
    users.insert_one(cleaned)
    return jsonify({"message": "User created"})

@app.route("/users", methods=["GET"])
def get_users():
    result = list(users.find())
    for u in result:
        u["_id"] = str(u["_id"])
    return jsonify(result)

@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    object_id = _parse_object_id(user_id)
    if object_id is None:
        return _bad_request("Invalid user id.")

    user = users.find_one({"_id": object_id})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user["_id"] = str(user["_id"])
    return jsonify(user)

@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    object_id = _parse_object_id(user_id)
    if object_id is None:
        return _bad_request("Invalid user id.")

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return _bad_request("Request body must be a non-empty JSON object.")

    users.update_one({"_id": object_id}, {"$set": data})
    return jsonify({"message": "User updated"})

@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    object_id = _parse_object_id(user_id)
    if object_id is None:
        return _bad_request("Invalid user id.")

    users.delete_one({"_id": object_id})
    return jsonify({"message": "User deleted"})


# ── Courses ────────────────────────────────────────────────────────────────────

@app.route("/courses", methods=["POST"])
def create_course():
    cleaned, error = validate_course_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    courses.insert_one(cleaned)
    return jsonify({"message": "Course created"})

@app.route("/courses", methods=["GET"])
def get_courses():
    result = list(courses.find())
    for c in result:
        c["_id"] = str(c["_id"])
    return jsonify(result)

@app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    object_id = _parse_object_id(course_id)
    if object_id is None:
        return _bad_request("Invalid course id.")

    course = courses.find_one({"_id": object_id})
    if not course:
        return jsonify({"error": "Course not found"}), 404
    course["_id"] = str(course["_id"])
    return jsonify(course)

@app.route("/courses/<course_id>", methods=["PUT"])
def update_course(course_id):
    object_id = _parse_object_id(course_id)
    if object_id is None:
        return _bad_request("Invalid course id.")

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return _bad_request("Request body must be a non-empty JSON object.")

    courses.update_one({"_id": object_id}, {"$set": data})
    return jsonify({"message": "Course updated"})

@app.route("/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    object_id = _parse_object_id(course_id)
    if object_id is None:
        return _bad_request("Invalid course id.")

    courses.delete_one({"_id": object_id})
    return jsonify({"message": "Course deleted"})


# ── API Keys ───────────────────────────────────────────────────────────────────

@app.route("/api_keys", methods=["POST"])
def create_api_key():
    cleaned, error = validate_api_key_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    cleaned["created"] = datetime.now(timezone.utc).isoformat()
    api_keys.insert_one(cleaned)
    return jsonify({"message": "API key created"})

@app.route("/api_keys", methods=["GET"])
def get_api_keys():
    result = list(api_keys.find())
    for k in result:
        k["_id"] = str(k["_id"])
    return jsonify(result)

@app.route("/api_keys/<key_id>", methods=["GET"])
def get_api_key(key_id):
    object_id = _parse_object_id(key_id)
    if object_id is None:
        return _bad_request("Invalid API key id.")

    key = api_keys.find_one({"_id": object_id})
    if not key:
        return jsonify({"error": "API key not found"}), 404
    key["_id"] = str(key["_id"])
    return jsonify(key)

@app.route("/api_keys/<key_id>", methods=["DELETE"])
def delete_api_key(key_id):
    object_id = _parse_object_id(key_id)
    if object_id is None:
        return _bad_request("Invalid API key id.")

    api_keys.delete_one({"_id": object_id})
    return jsonify({"message": "API key deleted"})

if __name__ == "__main__":
    app.run(debug=True, port = 5001)