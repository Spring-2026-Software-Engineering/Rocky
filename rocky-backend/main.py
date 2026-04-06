from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import sys
from typing import Any
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from backend.authz import require_admin, require_requester_identity
from backend.course_actions import (
    add_course_members,
    add_group_member,
    apply_course_metadata_patch,
    can_manage_api_keys,
    can_manage_metadata,
    can_manage_people,
    create_course_group,
    delete_course_api_keys,
    filter_visible_courses,
    get_course_record,
    remove_course_member,
    remove_group_member,
    regenerate_course_api_key,
)
from backend.config import get_settings
from backend.fixtures import read_seed_json
from backend.storage import Collections, build_collections
from backend.validation import (
    EMAIL_RE,
    normalize_str,
    validate_course_payload,
    validate_user_payload,
)

SEED_DATA_DIR = Path(__file__).resolve().parent / "seed-data"
if str(SEED_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(SEED_DATA_DIR))


def _load_seed_data_module():
    module_path = SEED_DATA_DIR / "seed_data.py"
    spec = importlib.util.spec_from_file_location("rocky_backend_seed_data", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load seed data module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_seed_data = _load_seed_data_module()
seed_data_database = _seed_data.seed_database
seed_data_static_content = _seed_data.seed_static_content

settings = get_settings()
app = Flask(__name__)
CORS(app)

collections: Collections = build_collections(settings)
users = collections.users
courses = collections.courses
api_keys = collections.api_keys
api_history = collections.api_history
analytics_kpis = collections.analytics_kpis
analytics_activity = collections.analytics_activity
widgets_default = collections.widgets_default
help_faq = collections.help_faq

ALLOWED_THEME_PREFERENCES = {"light", "dark", "system"}


def _parse_object_id(value: str):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _bad_request(message: str):
    return jsonify({"error": message}), 400


def _default_widgets_payload() -> list[dict[str, Any]]:
    rows = _get_collection_snapshot(widgets_default)
    widgets: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        widget_id = normalize_str(item.get("id")).lower()
        title = normalize_str(item.get("title")) or "Untitled Widget"
        html = normalize_str(item.get("html"))
        lines = item.get("lines") if isinstance(item.get("lines"), list) else []
        cleaned_lines = [normalize_str(line) for line in lines if normalize_str(line)]
        widget_doc: dict[str, Any] = {"title": title}
        if widget_id:
            widget_doc["id"] = widget_id
            widget_doc["widgetId"] = widget_id
            widget_doc["link"] = f"/widgets/default#{widget_id}"
        if html:
            widget_doc["html"] = html
        if cleaned_lines:
            widget_doc["lines"] = cleaned_lines
        widgets.append(widget_doc)
    return widgets


def _default_widget_ids() -> list[str]:
    return [widget_id for widget_id in (_widget_id(widget) for widget in _default_widgets_payload()) if widget_id]


def _default_user_settings() -> dict[str, Any]:
    return {
        "themePreference": "system",
        "widgets": _default_widget_ids(),
    }


def _widget_signature(widget: dict[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    title = normalize_str(widget.get("title")).lower()
    html = normalize_str(widget.get("html"))
    lines = widget.get("lines") if isinstance(widget.get("lines"), list) else []
    normalized_lines = tuple(normalize_str(line) for line in lines if normalize_str(line))
    return title, html, normalized_lines


def _widget_id(widget: dict[str, Any]) -> str:
    candidate = widget.get("widgetId") or widget.get("id")
    return normalize_str(candidate).lower()


def _canonical_available_widgets() -> list[dict[str, Any]]:
    return _default_widgets_payload()


def _expand_widget_selection(raw_widgets: Any) -> list[dict[str, Any]]:
    available_widgets = _canonical_available_widgets()
    available_by_id = {_widget_id(widget): widget for widget in available_widgets if _widget_id(widget)}
    expanded: list[dict[str, Any]] = []

    if not isinstance(raw_widgets, list):
        raw_widgets = []

    for item in raw_widgets:
        widget_id = ""
        if isinstance(item, str):
            widget_id = item.strip().lower()
        elif isinstance(item, dict):
            widget_id = _widget_id(item)

        canonical_widget = available_by_id.get(widget_id)
        if canonical_widget is not None:
            expanded.append(canonical_widget)

    return expanded


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


def _resolve_user_record(user_id: str | None, email: str | None):
    normalized_email = normalize_str(email).lower()
    if normalized_email and EMAIL_RE.match(normalized_email):
        user = users.find_one({"email": normalized_email})
        if user:
            return user

    normalized_user_id = normalize_str(user_id)
    if normalized_user_id:
        object_id = _parse_object_id(normalized_user_id)
        if object_id is not None:
            user = users.find_one({"_id": object_id})
            if user:
                return user

        user = users.find_one({"external_id": normalized_user_id})
        if user:
            return user

        user = users.find_one({"flash_id": normalized_user_id})
        if user:
            return user

    return None


def _can_access_user_record(requester_email: str, requester_role: str, target_user: dict[str, Any]) -> bool:
    if requester_role == "admin":
        return True
    return normalize_str(target_user.get("email")).lower() == normalize_str(requester_email).lower()


def _sanitize_widgets(raw: Any) -> list[dict[str, Any]]:
    available_widgets = _canonical_available_widgets()
    available_by_id = {_widget_id(widget): widget for widget in available_widgets if _widget_id(widget)}
    available_signatures = {_widget_signature(widget): widget for widget in available_widgets}

    if not isinstance(raw, list):
        return _default_widget_ids()

    widgets: list[str] = []
    for item in raw:
        widget_id = ""
        if isinstance(item, str):
            widget_id = item.strip().lower()
        elif isinstance(item, dict):
            widget_id = _widget_id(item)
            if not widget_id:
                signature = _widget_signature(item)
                canonical_widget = available_signatures.get(signature)
                if canonical_widget is not None:
                    widget_id = _widget_id(canonical_widget)

        if widget_id and widget_id in available_by_id:
            widgets.append(widget_id)

    return widgets or _default_widget_ids()


def _sanitize_user_settings(raw: Any):
    settings_payload = _default_user_settings()
    if isinstance(raw, dict):
        theme = normalize_str(raw.get("themePreference")).lower()
        if theme in ALLOWED_THEME_PREFERENCES:
            settings_payload["themePreference"] = theme

    raw_widgets = raw.get("widgets") if isinstance(raw, dict) else None
    settings_payload["widgets"] = _sanitize_widgets(raw_widgets)

    return settings_payload


def _resolve_user_settings(settings_payload: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(settings_payload)
    resolved["widgets"] = _expand_widget_selection(settings_payload.get("widgets"))
    return resolved


def _sanitize_user_settings_patch(raw: Any):
    if not isinstance(raw, dict):
        return {}, "patch must be a JSON object."

    patch: dict[str, Any] = {}
    if "themePreference" in raw:
        theme = normalize_str(raw.get("themePreference")).lower()
        if theme not in ALLOWED_THEME_PREFERENCES:
            allowed = ", ".join(sorted(ALLOWED_THEME_PREFERENCES))
            return {}, f"themePreference must be one of: {allowed}."
        patch["themePreference"] = theme

    if "widgets" in raw:
        patch["widgets"] = _sanitize_widgets(raw.get("widgets"))

    return patch, None


def _get_settings_for_user(user_record: dict[str, Any]):
    current = _sanitize_user_settings(user_record.get("settings"))
    users.update_one(
        {"_id": user_record["_id"]},
        {
            "$set": {
                "settings": current,
                "settings_updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return _resolve_user_settings(current)


def _upsert_settings_for_user(user_record: dict[str, Any], settings_payload: dict[str, Any]):
    users.update_one(
        {"_id": user_record["_id"]},
        {
            "$set": {
                "settings": settings_payload,
                "settings_updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


def seed_database(payload: dict[str, Any]) -> dict[str, int]:
	return seed_data_database(collections, payload)


def seed_static_content() -> dict[str, int]:
	return seed_data_static_content(collections, read_seed_json)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"ok": True, "env": settings.app_env})


@app.route("/", methods=["GET"])
def index_page():
    if settings.app_env == "production" and not settings.enable_db_inspector:
        return jsonify({"error": "Not found"}), 404

    collections_snapshot = {
        "users": {
            "docs": _get_collection_snapshot(users),
            "description": "Canonical user records; each user document owns its settings.",
        },
        "courses": {
            "docs": _get_collection_snapshot(courses),
            "description": "Course records and memberships.",
        },
        "api_keys": {
            "docs": _get_collection_snapshot(api_keys),
            "description": "Issued API keys.",
        },
        "api_history": {
            "docs": _get_collection_snapshot(api_history),
            "description": "Per-course API request history.",
        },
    }
    return render_template(
        "index.html",
        generated_at=datetime.now(timezone.utc).isoformat(),
        collections=collections_snapshot,
    )


@app.route("/auth/preview-users", methods=["GET"])
def get_preview_users():
    if not settings.enable_preview_login:
        return jsonify({"error": "Not found"}), 404

    result = list(users.find())
    for user in result:
        user["_id"] = str(user["_id"])
    return jsonify(result)


@app.route("/users", methods=["POST"])
def create_user():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    cleaned, error = validate_user_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
    cleaned["settings"] = _default_user_settings()
    cleaned["settings_updated_at"] = datetime.now(timezone.utc).isoformat()
    users.insert_one(cleaned)
    return jsonify({"message": "User created"})


@app.route("/users", methods=["GET"])
def get_users():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    result = list(users.find())
    for user in result:
        user["_id"] = str(user["_id"])
    return jsonify(result)


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

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
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

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
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    object_id = _parse_object_id(user_id)
    if object_id is None:
        return _bad_request("Invalid user id.")

    users.delete_one({"_id": object_id})
    return jsonify({"message": "User deleted"})


@app.route("/courses", methods=["POST"])
def create_course():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    cleaned, error = validate_course_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)
    if "id" not in cleaned:
        existing_ids = [course.get("id", 0) for course in courses.find() if isinstance(course.get("id"), int)]
        cleaned["id"] = (max(existing_ids) if existing_ids else 0) + 1

    courses.insert_one(cleaned)
    return jsonify(_serialize_value(cleaned)), 201


@app.route("/courses", methods=["GET"])
def get_courses():
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    result = [_serialize_value(course) for course in courses.find()]
    return jsonify(filter_visible_courses(result, email, role))


@app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    serialized = _serialize_value(course)
    visible = filter_visible_courses([serialized], email, role)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    return jsonify(visible[0])


@app.route("/courses/<course_id>/metadata", methods=["PATCH"])
def patch_course_metadata(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    if not can_manage_metadata(role):
        return jsonify({"error": "Admin role is required."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return _bad_request("Request body must be a non-empty JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    try:
        updated = apply_course_metadata_patch(course, users, data)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    courses.delete_one({"_id": course["_id"]})
    return jsonify({"message": "Course deleted"})


@app.route("/courses/<course_id>/members", methods=["POST"])
def add_course_members_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    data = request.get_json(silent=True)
    if data is None:
        return _bad_request("Request body is required.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, email, role):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    members_payload = data.get("members") if isinstance(data, dict) else data
    if isinstance(members_payload, dict):
        members_payload = [members_payload]

    try:
        updated = add_course_members(course, users, members_payload, role)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/members", methods=["DELETE"])
def remove_course_member_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    target_email = normalize_str(data.get("email") or data.get("memberEmail")).lower()
    if not target_email:
        return _bad_request("email is required.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, email, role):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    try:
        updated = remove_course_member(course, target_email, role)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/groups", methods=["POST"])
def create_course_group_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, email, role):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    try:
        updated = create_course_group(course, data.get("name", ""))
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/groups/<group_id>/members", methods=["POST"])
def add_group_member_route(course_id, group_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, email, role):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    target_email = normalize_str(data.get("email") or data.get("memberEmail")).lower()
    if not target_email:
        return _bad_request("email is required.")

    try:
        updated = add_group_member(course, group_id, target_email)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/groups/<group_id>/members", methods=["DELETE"])
def remove_group_member_route(course_id, group_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, email, role):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    target_email = normalize_str(data.get("email") or data.get("memberEmail")).lower()
    if not target_email:
        return _bad_request("email is required.")

    try:
        updated = remove_group_member(course, group_id, target_email)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/api-key/regenerate", methods=["POST"])
def regenerate_course_api_key_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    if not can_manage_api_keys(role):
        return jsonify({"error": "Admin role is required."}), 403

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    try:
        key_doc = regenerate_course_api_key(course, api_keys, email)
    except ValueError as exc:
        return _bad_request(str(exc))

    return jsonify(_serialize_value(key_doc))


@app.route("/courses/<course_id>/api-key", methods=["DELETE"])
def delete_course_api_key_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    _, role = identity
    if not can_manage_api_keys(role):
        return jsonify({"error": "Admin role is required."}), 403

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    try:
        deleted_count = delete_course_api_keys(course, api_keys)
    except ValueError as exc:
        return _bad_request(str(exc))

    return jsonify({"message": "API keys deleted", "deleted": deleted_count})


@app.route("/user-settings", methods=["GET"])
def get_user_settings():
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    user_record = _resolve_user_record(request.args.get("userId"), request.args.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, role, user_record):
        return jsonify({"error": "You may only access your own settings."}), 403

    settings_payload = _get_settings_for_user(user_record)
    return jsonify({"settings": settings_payload})


@app.route("/user-settings", methods=["PATCH"])
def patch_user_settings():
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    user_record = _resolve_user_record(data.get("userId"), data.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, role, user_record):
        return jsonify({"error": "You may only access your own settings."}), 403

    patch, patch_error = _sanitize_user_settings_patch(data.get("patch"))
    if patch_error:
        return _bad_request(patch_error)

    current = _sanitize_user_settings(user_record.get("settings"))
    updated = {**current, **patch}
    _upsert_settings_for_user(user_record, updated)
    return jsonify({"settings": _resolve_user_settings(updated)})


@app.route("/user-settings/<setting_key>", methods=["PATCH"])
def patch_user_setting(setting_key):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    user_record = _resolve_user_record(data.get("userId"), data.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, role, user_record):
        return jsonify({"error": "You may only access your own settings."}), 403

    if setting_key != "themePreference":
        return _bad_request(f"Unsupported user setting key: {setting_key}.")

    value = normalize_str(data.get("value")).lower()
    if value not in ALLOWED_THEME_PREFERENCES:
        allowed = ", ".join(sorted(ALLOWED_THEME_PREFERENCES))
        return _bad_request(f"themePreference must be one of: {allowed}.")

    current = _sanitize_user_settings(user_record.get("settings"))
    current["themePreference"] = value
    _upsert_settings_for_user(user_record, current)
    return jsonify({"settings": _resolve_user_settings(current)})


def _build_api_history_entry(course: dict[str, Any], requester_email: str, payload: dict[str, Any]) -> dict[str, Any]:
    requester = requester_email.lower()
    groups = course.get("groups") if isinstance(course.get("groups"), list) else []
    matched_group = next(
        (
            group
            for group in groups
            if isinstance(group, dict)
            and requester in [normalize_str(email).lower() for email in (group.get("memberEmails") or [])]
        ),
        None,
    )

    group_id = normalize_str(payload.get("groupId")) or (normalize_str(matched_group.get("id")) if matched_group else "")
    group_name = normalize_str(payload.get("groupName")) or (normalize_str(matched_group.get("name")) if matched_group else "")

    return {
        "u_id": requester,
        "c_id": normalize_str(course.get("code")),
        "course_id": course.get("id"),
        "event_type": normalize_str(payload.get("eventType")) or "request",
        "group_id": group_id or None,
        "group_name": group_name or None,
        "is_group_member": bool(group_id),
        "meta": payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
        "created": datetime.now(timezone.utc).isoformat(),
    }


@app.route("/courses/<course_id>/api-history", methods=["POST"])
def append_course_api_history(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    visible = filter_visible_courses([_serialize_value(course)], email, role)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return _bad_request("Request body must be a JSON object.")

    history_doc = _build_api_history_entry(course, email, payload)
    api_history.insert_one(history_doc)
    return jsonify(_serialize_value(history_doc)), 201


@app.route("/courses/<course_id>/api-history", methods=["GET"])
def get_course_api_history(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    visible = filter_visible_courses([_serialize_value(course)], email, role)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    query = {"c_id": normalize_str(course.get("code"))}
    if not can_manage_people(course, email, role):
        query["u_id"] = email.lower()

    rows = [_serialize_value(item) for item in api_history.find(query)]
    return jsonify(rows)


@app.route("/analytics/kpis", methods=["GET"])
def get_analytics_kpis():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    return jsonify(_get_collection_snapshot(analytics_kpis))


@app.route("/analytics/activity", methods=["GET"])
def get_analytics_activity():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    return jsonify(_get_collection_snapshot(analytics_activity))


@app.route("/widgets/default", methods=["GET"])
def get_default_widgets():
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, role = identity

    user_record = _resolve_user_record(None, email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, role, user_record):
        return jsonify({"error": "You may only access your own widgets."}), 403

    settings_payload = _get_settings_for_user(user_record)
    return jsonify(settings_payload.get("widgets", []))


@app.route("/help/faq", methods=["GET"])
def get_help_faq():
    return jsonify(_get_collection_snapshot(help_faq))


if __name__ == "__main__":
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
