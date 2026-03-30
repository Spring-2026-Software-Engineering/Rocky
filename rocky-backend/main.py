import re
import json
import os
from typing import Any
from pathlib import Path

from flask import Flask
from flask import request, jsonify, render_template
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
user_settings = db["user_settings"]

ALLOWED_USER_ROLES = {"student", "instructor", "admin", "client"}
ALLOWED_TERMS = {"spring", "summer", "fall", "winter"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_THEME_PREFERENCES = {"light", "dark", "system"}

LOCAL_API_ROOT = (Path(__file__).resolve().parents[1] / "rocky-interface" / "static" / "local-api").resolve()


def _normalize_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _parse_object_id(value: str):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _bad_request(message: str):
    return jsonify({"error": message}), 400


def _default_user_settings() -> dict[str, str]:
    return {"themePreference": "system"}


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _serialize_value(value: Any):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    return value


def _get_collection_snapshot(collection):
    return [_serialize_value(item) for item in collection.find()]


def _read_local_api_json(*segments: str):
    file_path = LOCAL_API_ROOT.joinpath(*segments)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_user_scope(user_id: str | None, email: str | None):
    normalized_user_id = _normalize_str(user_id).lower()
    if normalized_user_id:
        return f"id:{normalized_user_id}", None

    normalized_email = _normalize_str(email).lower()
    if not normalized_email or not EMAIL_RE.match(normalized_email):
        return None, "A valid userId or email is required."
    return f"email:{normalized_email}", None


def _sanitize_user_settings(raw: Any):
    settings = _default_user_settings()
    if isinstance(raw, dict):
        theme = _normalize_str(raw.get("themePreference")).lower()
        if theme in ALLOWED_THEME_PREFERENCES:
            settings["themePreference"] = theme
    return settings


def _sanitize_user_settings_patch(raw: Any):
    if not isinstance(raw, dict):
        return {}, "patch must be a JSON object."

    patch: dict[str, str] = {}
    if "themePreference" in raw:
        theme = _normalize_str(raw.get("themePreference")).lower()
        if theme not in ALLOWED_THEME_PREFERENCES:
            allowed = ", ".join(sorted(ALLOWED_THEME_PREFERENCES))
            return {}, f"themePreference must be one of: {allowed}."
        patch["themePreference"] = theme

    return patch, None


def _get_settings_for_scope(scope: str):
    record = user_settings.find_one({"scope": scope})
    if not record:
        return _default_user_settings()
    return _sanitize_user_settings(record.get("settings"))


def _upsert_settings_for_scope(scope: str, settings: dict[str, str]):
    document = {
        "scope": scope,
        "settings": settings,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    existing = user_settings.find_one({"scope": scope})
    if existing:
        user_settings.replace_one({"_id": existing["_id"]}, document)
    else:
        user_settings.insert_one(document)


def _semester_display(term: str, year: int) -> str:
    return f"{term.capitalize()} {year}"


def _parse_semester(value: Any):
    if isinstance(value, dict):
        year = value.get("year")
        term = _normalize_str(value.get("term")).lower()
        if not isinstance(year, int) or year < 2000 or year > 2100:
            return None, "semester.year must be an integer between 2000 and 2100."
        if term not in ALLOWED_TERMS:
            allowed_terms = ", ".join(sorted(ALLOWED_TERMS))
            return None, f"semester.term must be one of: {allowed_terms}."
        return {"year": year, "term": term, "display": _semester_display(term, year)}, None

    if isinstance(value, str):
        parts = value.strip().split()
        if len(parts) != 2:
            return None, "semester string must look like 'Fall 2026'."
        term = parts[0].lower()
        try:
            year = int(parts[1])
        except ValueError:
            return None, "semester year in string format must be an integer."
        if term not in ALLOWED_TERMS:
            allowed_terms = ", ".join(sorted(ALLOWED_TERMS))
            return None, f"semester term in string format must be one of: {allowed_terms}."
        if year < 2000 or year > 2100:
            return None, "semester year in string format must be between 2000 and 2100."
        return {"year": year, "term": term, "display": _semester_display(term, year)}, None

    return None, "semester must be either an object {year, term} or a string like 'Fall 2026'."


def _normalize_course_members(value: Any):
    if value is None:
        return [], [], [], None
    if not isinstance(value, list):
        return None, None, None, "members must be a list."

    members = []
    instructor_ids = []
    student_ids = []
    for entry in value:
        if not isinstance(entry, dict):
            return None, None, None, "each member must be an object."

        account_email = _normalize_str(entry.get("accountEmail") or entry.get("email")).lower()
        if not account_email or not EMAIL_RE.match(account_email):
            return None, None, None, "each member must include a valid accountEmail/email."

        role = _normalize_str(entry.get("role") or "student").lower()
        if role not in {"student", "instructor"}:
            return None, None, None, "member role must be 'student' or 'instructor'."

        normalized = {
            "accountEmail": account_email,
            "email": account_email,
            "role": role,
        }
        members.append(normalized)
        if role == "instructor":
            instructor_ids.append(account_email)
        else:
            student_ids.append(account_email)

    return members, instructor_ids, student_ids, None


def _normalize_course_groups(value: Any):
    if value is None:
        return [], None
    if not isinstance(value, list):
        return None, "groups must be a list."

    groups = []
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, "each group must be an object."

        group_id = _normalize_str(entry.get("id")) or f"group-{index}"
        name = _normalize_str(entry.get("name"))
        if not name:
            return None, "each group requires a name."

        member_emails = entry.get("memberEmails")
        if not isinstance(member_emails, list):
            return None, "group.memberEmails must be a list."

        normalized_emails = []
        for email in member_emails:
            email_value = _normalize_str(email).lower()
            if not email_value or not EMAIL_RE.match(email_value):
                return None, "group.memberEmails entries must be valid email strings."
            normalized_emails.append(email_value)

        groups.append({"id": group_id, "name": name, "memberEmails": normalized_emails})

    return groups, None


def validate_user_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    name = _normalize_str(payload.get("name"))
    email = _normalize_str(payload.get("email")).lower()
    flash_id = _normalize_str(payload.get("flash_id"))
    role = _normalize_str(payload.get("role")).lower()
    external_id = _normalize_str(payload.get("_id"))

    if not name:
        return None, "User name is required."
    if not email or not EMAIL_RE.match(email):
        return None, "A valid user email is required."
    if not flash_id:
        flash_id = f"seed-{email.split('@')[0]}"
    if role not in ALLOWED_USER_ROLES:
        allowed_roles = ", ".join(sorted(ALLOWED_USER_ROLES))
        return None, f"Invalid role. Allowed values: {allowed_roles}."

    cleaned = {
        "name": name,
        "email": email,
        "flash_id": flash_id,
        "role": role,
    }
    if external_id:
        cleaned["external_id"] = external_id

    return cleaned, None


def validate_course_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    name = _normalize_str(payload.get("name"))
    semester_value = payload.get("semester")
    parsed_semester, semester_error = _parse_semester(semester_value)
    if semester_error:
        return None, semester_error

    if not name:
        return None, "Course name is required."

    members, member_instructors, member_students, member_error = _normalize_course_members(payload.get("members"))
    if member_error:
        return None, member_error

    groups, groups_error = _normalize_course_groups(payload.get("groups"))
    if groups_error:
        return None, groups_error

    instructor_ids = payload.get("instructor_ids")
    student_ids = payload.get("student_ids")

    # Legacy input path: accepts explicit ids when members are not supplied.
    if instructor_ids is None:
        instructor_ids = member_instructors
    if student_ids is None:
        student_ids = member_students

    if not isinstance(instructor_ids, list) or not all(isinstance(v, str) and v.strip() for v in instructor_ids):
        return None, "instructor_ids must be a list of non-empty strings."
    if not isinstance(student_ids, list) or not all(isinstance(v, str) and v.strip() for v in student_ids):
        return None, "student_ids must be a list of non-empty strings."

    announcements = payload.get("announcements")
    if announcements is None:
        announcements = []
    if not isinstance(announcements, list) or not all(isinstance(v, str) for v in announcements):
        return None, "announcements must be a list of strings."

    course_code = _normalize_str(payload.get("code"))
    instructor_name = _normalize_str(payload.get("instructor"))
    color = _normalize_str(payload.get("color")) or "#1a4a8a"
    overview = _normalize_str(payload.get("overview"))

    cleaned = {
        "name": name,
        "instructor_ids": [v.strip().lower() for v in instructor_ids],
        "student_ids": [v.strip().lower() for v in student_ids],
        "semester": parsed_semester["display"],
        "semester_obj": {"year": parsed_semester["year"], "term": parsed_semester["term"]},
        "members": members,
        "groups": groups,
        "announcements": [v.strip() for v in announcements],
        "overview": overview,
        "color": color,
    }

    if course_code:
        cleaned["code"] = course_code
    if instructor_name:
        cleaned["instructor"] = instructor_name

    course_id = payload.get("id")
    if isinstance(course_id, int):
        cleaned["id"] = course_id

    return cleaned, None


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


@app.route("/", methods=["GET"])
def index_page():
    # This inspector page is intended for local/test debugging only.
    if not _is_truthy(os.getenv("ROCKY_ENABLE_DB_INSPECTOR", "true")):
        return jsonify({"error": "Not found"}), 404

    collections = {
        "users": _get_collection_snapshot(users),
        "courses": _get_collection_snapshot(courses),
        "api_keys": _get_collection_snapshot(api_keys),
        "user_settings": _get_collection_snapshot(user_settings),
    }
    return render_template(
        "index.html",
        generated_at=datetime.now(timezone.utc).isoformat(),
        collections=collections,
    )


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


# ── User Settings ──────────────────────────────────────────────────────────────

@app.route("/user-settings", methods=["GET"])
def get_user_settings():
    scope, error = _build_user_scope(request.args.get("userId"), request.args.get("email"))
    if error:
        return _bad_request(error)

    settings = _get_settings_for_scope(scope)
    return jsonify({"settings": settings})


@app.route("/user-settings", methods=["PATCH"])
def patch_user_settings():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    scope, error = _build_user_scope(data.get("userId"), data.get("email"))
    if error:
        return _bad_request(error)

    patch, patch_error = _sanitize_user_settings_patch(data.get("patch"))
    if patch_error:
        return _bad_request(patch_error)

    current = _get_settings_for_scope(scope)
    updated = {**current, **patch}
    _upsert_settings_for_scope(scope, updated)
    return jsonify({"settings": updated})


@app.route("/user-settings/<setting_key>", methods=["PATCH"])
def patch_user_setting(setting_key):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    scope, error = _build_user_scope(data.get("userId"), data.get("email"))
    if error:
        return _bad_request(error)

    if setting_key != "themePreference":
        return _bad_request(f"Unsupported user setting key: {setting_key}.")

    value = _normalize_str(data.get("value")).lower()
    if value not in ALLOWED_THEME_PREFERENCES:
        allowed = ", ".join(sorted(ALLOWED_THEME_PREFERENCES))
        return _bad_request(f"themePreference must be one of: {allowed}.")

    current = _get_settings_for_scope(scope)
    current["themePreference"] = value
    _upsert_settings_for_scope(scope, current)
    return jsonify({"settings": current})


# ── Analytics & Widgets ───────────────────────────────────────────────────────

@app.route("/analytics/kpis", methods=["GET"])
def get_analytics_kpis():
    try:
        return jsonify(_read_local_api_json("analytics", "kpis.json"))
    except FileNotFoundError:
        return jsonify({"error": "Analytics KPI data not found."}), 404


@app.route("/analytics/activity", methods=["GET"])
def get_analytics_activity():
    try:
        return jsonify(_read_local_api_json("analytics", "activity.json"))
    except FileNotFoundError:
        return jsonify({"error": "Analytics activity data not found."}), 404


@app.route("/widgets/default", methods=["GET"])
def get_default_widgets():
    try:
        return jsonify(_read_local_api_json("widgets", "default.json"))
    except FileNotFoundError:
        return jsonify({"error": "Default widgets data not found."}), 404

if __name__ == "__main__":
    app.run(debug=True, port = 5001)