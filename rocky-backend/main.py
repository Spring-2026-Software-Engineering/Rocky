from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import random
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
whitelist_users = collections.whitelist_users
courses = collections.courses
api_keys = collections.api_keys
api_history = collections.api_history
analytics_kpis = collections.analytics_kpis
analytics_activity = collections.analytics_activity
widgets_default = collections.widgets_default
help_faq = collections.help_faq

ALLOWED_THEME_PREFERENCES = {"light", "dark", "system"}
KENT_EMAIL_SUFFIX = "@kent.edu"
WLID_PREFIX = "WLID"
KSUID_PREFIX = "KSUID"


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

        whitelist_user = whitelist_users.find_one({"email": normalized_email})
        if whitelist_user:
            return {
                "id": normalize_str(whitelist_user.get("id")),
                "first_name": normalize_str(whitelist_user.get("first_name")),
                "last_name": normalize_str(whitelist_user.get("last_name")),
                "email": normalized_email,
                "is_admin": bool(whitelist_user.get("is_admin")),
                "is_active": _is_user_active(whitelist_user),
                "settings": whitelist_user.get("settings", _default_user_settings()),
                "created_at": whitelist_user.get("created_at"),
            }

    normalized_user_id = normalize_str(user_id)
    if normalized_user_id:
        user = users.find_one({"id": normalized_user_id})
        if user:
            return user

        whitelist_user = whitelist_users.find_one({"id": normalized_user_id})
        if whitelist_user:
            return {
                "id": normalize_str(whitelist_user.get("id")),
                "first_name": normalize_str(whitelist_user.get("first_name")),
                "last_name": normalize_str(whitelist_user.get("last_name")),
                "email": normalize_str(whitelist_user.get("email")).lower(),
                "is_admin": bool(whitelist_user.get("is_admin")),
                "is_active": _is_user_active(whitelist_user),
                "settings": whitelist_user.get("settings", _default_user_settings()),
                "created_at": whitelist_user.get("created_at"),
            }

    return None


def _is_user_active(user_record: dict[str, Any]) -> bool:
    if "is_active" not in user_record:
        return True
    return bool(user_record.get("is_active"))


def _is_kent_email(email: str) -> bool:
    return email.lower().endswith(KENT_EMAIL_SUFFIX)


def _coerce_ksuid(value: str | None) -> str:
    raw = normalize_str(value).upper()
    if not raw:
        return ""

    if raw.startswith(KSUID_PREFIX):
        suffix = raw[len(KSUID_PREFIX):]
        return f"{KSUID_PREFIX}{suffix}" if suffix.isdigit() and len(suffix) == 9 else ""

    return f"{KSUID_PREFIX}{raw}" if raw.isdigit() and len(raw) == 9 else ""


def _next_prefixed_id(collection, field_name: str, prefix: str) -> str:
    while True:
        candidate = f"{prefix}{random.randint(0, 999999999):09d}"
        if collection.find_one({field_name: candidate}) is None:
            return candidate


def _wlid_exists(candidate: str) -> bool:
    return (
        whitelist_users.find_one({"id": candidate}) is not None
        or users.find_one({"id": candidate}) is not None
    )


def _next_unique_wlid() -> str:
    while True:
        candidate = f"{WLID_PREFIX}{random.randint(0, 999999999):09d}"
        if not _wlid_exists(candidate):
            return candidate


def _normalize_oauth_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    first_name = normalize_str(payload.get("firstName") or payload.get("first_name"))
    last_name = normalize_str(payload.get("lastName") or payload.get("last_name"))
    email = normalize_str(payload.get("email")).lower()
    user_id = normalize_str(payload.get("id"))

    if not email or not EMAIL_RE.match(email):
        return None, "A valid OAuth email is required."
    if not first_name and not last_name:
        return None, "At least one of firstName or lastName is required."

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "id": user_id,
    }, None


def _build_display_name(first_name: str, last_name: str, email: str) -> str:
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    return email.split("@", 1)[0]


def _resolve_requester_user_id(email: str) -> str:
    user_record = _resolve_user_record(None, email)
    if user_record:
        user_id = normalize_str(user_record.get("id"))
        if user_id:
            return user_id
    return normalize_str(email).lower()


def _serialize_user(user_record: dict[str, Any]) -> dict[str, Any]:
    first_name = normalize_str(user_record.get("first_name"))
    last_name = normalize_str(user_record.get("last_name"))

    return _serialize_value(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": normalize_str(user_record.get("email")).lower(),
            "id": normalize_str(user_record.get("id")),
            "is_admin": bool(user_record.get("is_admin")),
            "is_active": _is_user_active(user_record),
            "created_at": user_record.get("created_at"),
            "settings": user_record.get("settings", _default_user_settings()),
        }
    )


def _serialize_whitelist_user(entry: dict[str, Any]) -> dict[str, Any]:
    return _serialize_value(
        {
            "first_name": normalize_str(entry.get("first_name")),
            "last_name": normalize_str(entry.get("last_name")),
            "email": normalize_str(entry.get("email")).lower(),
            "id": normalize_str(entry.get("id")),
            "is_admin": bool(entry.get("is_admin")),
            "is_active": _is_user_active(entry),
            "settings": entry.get("settings", _default_user_settings()),
            "created_at": entry.get("created_at"),
            "created_by": entry.get("created_by"),
        }
    )


def _can_access_user_record(requester_email: str, requester_is_admin: bool, target_user: dict[str, Any]) -> bool:
    if requester_is_admin:
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
    existing = users.find_one({"id": user_record["id"]})
    if existing:
        users.update_one(
            {"id": user_record["id"]},
            {
                "$set": {
                    "settings": current,
                }
            },
        )
    else:
        created_at = datetime.now(timezone.utc).isoformat()
        users.insert_one(
            {
                "id": user_record["id"],
                "first_name": normalize_str(user_record.get("first_name")),
                "last_name": normalize_str(user_record.get("last_name")),
                "email": normalize_str(user_record.get("email")).lower(),
                "is_admin": bool(user_record.get("is_admin")),
                "is_active": _is_user_active(user_record),
                "created_at": user_record.get("created_at") or created_at,
                "settings": current,
            }
        )
    return _resolve_user_settings(current)


def _upsert_settings_for_user(user_record: dict[str, Any], settings_payload: dict[str, Any]):
    existing = users.find_one({"id": user_record["id"]})
    if existing:
        users.update_one(
            {"id": user_record["id"]},
            {
                "$set": {
                    "settings": settings_payload,
                }
            },
        )
    else:
        created_at = datetime.now(timezone.utc).isoformat()
        users.insert_one(
            {
                "id": user_record["id"],
                "first_name": normalize_str(user_record.get("first_name")),
                "last_name": normalize_str(user_record.get("last_name")),
                "email": normalize_str(user_record.get("email")).lower(),
                "is_admin": bool(user_record.get("is_admin")),
                "is_active": _is_user_active(user_record),
                "created_at": user_record.get("created_at") or created_at,
                "settings": settings_payload,
            }
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
        "whitelist_users": {
            "docs": _get_collection_snapshot(whitelist_users),
            "description": "Approved non-@kent.edu addresses for Microsoft OAuth login.",
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

    result = [_serialize_user(user) for user in users.find()]
    known_emails = {normalize_str(user.get("email")).lower() for user in result if isinstance(user, dict)}
    for entry in whitelist_users.find():
        email = normalize_str(entry.get("email")).lower()
        if not email or email in known_emails:
            continue
        result.append(
            _serialize_user(
                {
                    "id": normalize_str(entry.get("id")),
                    "first_name": normalize_str(entry.get("first_name")),
                    "last_name": normalize_str(entry.get("last_name")),
                    "email": email,
                    "is_admin": bool(entry.get("is_admin")),
                    "is_active": _is_user_active(entry),
                    "settings": entry.get("settings", _default_user_settings()),
                    "created_at": entry.get("created_at"),
                }
            )
        )
    return jsonify(result)


@app.route("/auth/session-user", methods=["GET"])
def get_session_user():
    email = normalize_str(request.args.get("email")).lower()
    if not email or not EMAIL_RE.match(email):
        return _bad_request("A valid email query parameter is required.")

    user_record = _resolve_user_record(None, email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404

    return jsonify(_serialize_user(user_record))


@app.route("/auth/microsoft/login", methods=["POST"])
def microsoft_login():
    if not settings.enable_microsoft_oauth:
        return jsonify({"error": "Not found"}), 404

    cleaned, payload_error = _normalize_oauth_payload(request.get_json(silent=True))
    if payload_error:
        print(f"[oauth] login denied: invalid payload ({payload_error})", flush=True)
        return _bad_request(payload_error)

    email = cleaned["email"]
    first_name = cleaned["first_name"]
    last_name = cleaned["last_name"]
    if _is_kent_email(email):
        user_record = _resolve_user_record(None, email)
        generated_id = _coerce_ksuid(cleaned.get("id")) or _next_prefixed_id(users, "id", KSUID_PREFIX)

        if not user_record:
            to_insert = {
                "id": generated_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "is_admin": False,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "settings": _default_user_settings(),
            }
            users.insert_one(to_insert)
            user_record = users.find_one({"id": generated_id})
            print(f"[oauth] login success: created Kent user {email}", flush=True)
        else:
            users.update_one(
                {"id": user_record["id"]},
                {
                    "$set": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "id": user_record.get("id") or generated_id,
                    }
                },
            )
            user_record = users.find_one({"id": user_record["id"]})
            print(f"[oauth] login success: existing Kent user {email}", flush=True)

        return jsonify({"ok": True, "user": _serialize_user(user_record)})

    whitelist_record = whitelist_users.find_one({"email": email})
    if not whitelist_record:
        print(f"[oauth] login denied: non-Kent email not whitelisted ({email})", flush=True)
        return jsonify({"error": "This email is not approved for access."}), 403

    user_record = users.find_one({"email": email})
    if not user_record:
        external_id = normalize_str(whitelist_record.get("id"))
        whitelist_is_active = _is_user_active(whitelist_record)
        to_insert = {
            "id": external_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_admin": False,
            "is_active": whitelist_is_active,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "settings": _default_user_settings(),
        }
        users.insert_one(to_insert)
        user_record = users.find_one({"id": external_id})
        print(f"[oauth] login success: created whitelisted user {email}", flush=True)
    else:
        whitelist_is_active = _is_user_active(whitelist_record)
        users.update_one(
            {"id": user_record["id"]},
            {
                "$set": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "id": whitelist_record["id"],
                    "is_active": whitelist_is_active,
                }
            },
        )
        user_record = users.find_one({"id": user_record["id"]})
        print(f"[oauth] login success: existing whitelisted user {email}", flush=True)

    return jsonify({"ok": True, "user": _serialize_user(user_record)})


@app.route("/auth/microsoft/whitelist", methods=["GET"])
def get_oauth_whitelist():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    result = [_serialize_whitelist_user(entry) for entry in whitelist_users.find()]
    return jsonify(result)


@app.route("/auth/microsoft/whitelist", methods=["POST"])
def add_oauth_whitelist_entry():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _bad_request("Request body must be a JSON object.")

    first_name = normalize_str(payload.get("firstName") or payload.get("first_name"))
    last_name = normalize_str(payload.get("lastName") or payload.get("last_name"))
    email = normalize_str(payload.get("email")).lower()

    if not first_name:
        return _bad_request("firstName is required.")
    if not last_name:
        return _bad_request("lastName is required.")
    if not email or not EMAIL_RE.match(email):
        return _bad_request("A valid email is required.")
    if _is_kent_email(email):
        return _bad_request("@kent.edu emails should not be added to the external whitelist.")

    existing = whitelist_users.find_one({"email": email})
    if existing:
        print(f"[oauth] whitelist unchanged: entry already exists for {email}", flush=True)
        return jsonify({"message": "Whitelist entry already exists.", "entry": _serialize_whitelist_user(existing)})

    identity = require_requester_identity()
    requester_email = ""
    if identity[0] is not None:
        requester_email, _ = identity

    created = {
        "id": _next_unique_wlid(),
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "is_admin": False,
        "is_active": True,
        "settings": _default_user_settings(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": requester_email,
    }
    whitelist_users.insert_one(created)
    saved = whitelist_users.find_one({"id": created["id"]})

    print(f"[oauth] whitelist add success: {email}", flush=True)
    return jsonify({"message": "Whitelist entry added.", "entry": _serialize_whitelist_user(saved)}), 201


@app.route("/auth/microsoft/whitelist/<entry_id>", methods=["PATCH", "DELETE"])
def update_or_delete_oauth_whitelist_entry(entry_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    normalized_entry_id = normalize_str(entry_id)
    if not normalized_entry_id:
        return _bad_request("Invalid whitelist entry id.")

    entry = whitelist_users.find_one({"id": normalized_entry_id})
    if not entry:
        return jsonify({"error": "Whitelist entry not found"}), 404

    if request.method == "PATCH":
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _bad_request("Request body must be a JSON object.")
        if "is_active" not in payload:
            return _bad_request("is_active is required.")
        if not isinstance(payload.get("is_active"), bool):
            return _bad_request("is_active must be a boolean.")

        is_active = bool(payload.get("is_active"))
        whitelist_users.update_one({"id": normalized_entry_id}, {"$set": {"is_active": is_active}})
        users.update_one({"id": normalized_entry_id}, {"$set": {"is_active": is_active}})
        updated = whitelist_users.find_one({"id": normalized_entry_id})
        return jsonify({"message": "Whitelist user updated.", "entry": _serialize_whitelist_user(updated)})

    return jsonify({"error": "Whitelist deletion is disabled. Use account activation controls."}), 405


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
    cleaned["is_active"] = True
    users.insert_one(cleaned)
    return jsonify({"message": "User created"})


@app.route("/users", methods=["GET"])
def get_users():
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    result = [_serialize_user(user) for user in users.find()]
    return jsonify(result)


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    user = _resolve_user_record(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_serialize_user(user))


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    user = _resolve_user_record(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return _bad_request("Request body must be a non-empty JSON object.")

    if set(data.keys()) != {"is_active"}:
        return _bad_request("Only is_active may be updated through this endpoint.")
    if not isinstance(data.get("is_active"), bool):
        return _bad_request("is_active must be a boolean.")

    is_active = bool(data.get("is_active"))
    users.update_one({"id": user["id"]}, {"$set": {"is_active": is_active}})
    whitelist_users.update_one({"id": user["id"]}, {"$set": {"is_active": is_active}})
    return jsonify({"message": "User updated"})


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    user = _resolve_user_record(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"error": "User deletion is disabled. Use account activation controls."}), 405


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
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)
    result = [_serialize_value(course) for course in courses.find()]
    return jsonify(filter_visible_courses(result, requester_id or email, is_admin))


@app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)
    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    serialized = _serialize_value(course)
    visible = filter_visible_courses([serialized], requester_id or email, is_admin)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    return jsonify(visible[0])


@app.route("/courses/<course_id>/metadata", methods=["PATCH"])
def patch_course_metadata(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    _, is_admin = identity
    if not can_manage_metadata(is_admin):
        return jsonify({"error": "Admin access is required."}), 403

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
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    data = request.get_json(silent=True)
    if data is None:
        return _bad_request("Request body is required.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    members_payload = data.get("members") if isinstance(data, dict) else data
    if isinstance(members_payload, dict):
        members_payload = [members_payload]

    try:
        updated = add_course_members(course, users, members_payload, is_admin)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/members", methods=["DELETE"])
def remove_course_member_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    target_member_id = normalize_str(data.get("id") or data.get("memberId") or data.get("member_id"))
    if not target_member_id:
        return _bad_request("id is required.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    try:
        updated = remove_course_member(course, target_member_id, is_admin)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/groups", methods=["POST"])
def create_course_group_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, requester_id or email, is_admin):
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
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    target_member_id = normalize_str(data.get("id") or data.get("memberId") or data.get("member_id"))
    if not target_member_id:
        return _bad_request("id is required.")

    try:
        updated = add_group_member(course, group_id, target_member_id)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/groups/<group_id>/members", methods=["DELETE"])
def remove_group_member_route(course_id, group_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    target_member_id = normalize_str(data.get("id") or data.get("memberId") or data.get("member_id"))
    if not target_member_id:
        return _bad_request("id is required.")

    try:
        updated = remove_group_member(course, group_id, target_member_id)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


@app.route("/courses/<course_id>/api-key/regenerate", methods=["POST"])
def regenerate_course_api_key_route(course_id):
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    if not can_manage_api_keys(is_admin):
        return jsonify({"error": "Admin access is required."}), 403

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
    _, is_admin = identity
    if not can_manage_api_keys(is_admin):
        return jsonify({"error": "Admin access is required."}), 403

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
    email, is_admin = identity
    user_record = _resolve_user_record(request.args.get("userId"), request.args.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, is_admin, user_record):
        return jsonify({"error": "You may only access your own settings."}), 403

    settings_payload = _get_settings_for_user(user_record)
    return jsonify({"settings": settings_payload})


@app.route("/user-settings", methods=["PATCH"])
def patch_user_settings():
    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    user_record = _resolve_user_record(data.get("userId"), data.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, is_admin, user_record):
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
    email, is_admin = identity
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    user_record = _resolve_user_record(data.get("userId"), data.get("email") or email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, is_admin, user_record):
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
    requester_id = _resolve_requester_user_id(requester_email)
    groups = course.get("groups") if isinstance(course.get("groups"), list) else []
    matched_group = next(
        (
            group
            for group in groups
            if isinstance(group, dict)
            and requester_id in [normalize_str(member_id) for member_id in (group.get("memberIds") or group.get("memberEmails") or [])]
        ),
        None,
    )

    group_id = normalize_str(payload.get("groupId")) or (normalize_str(matched_group.get("id")) if matched_group else "")
    group_name = normalize_str(payload.get("groupName")) or (normalize_str(matched_group.get("name")) if matched_group else "")

    return {
        "u_id": requester_id,
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
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    visible = filter_visible_courses([_serialize_value(course)], requester_id or email, is_admin)
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
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    visible = filter_visible_courses([_serialize_value(course)], requester_id or email, is_admin)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    query = {"c_id": normalize_str(course.get("code"))}
    if not can_manage_people(course, requester_id or email, is_admin):
        query["u_id"] = _resolve_requester_user_id(email)

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
    email, is_admin = identity

    user_record = _resolve_user_record(None, email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404
    if not _can_access_user_record(email, is_admin, user_record):
        return jsonify({"error": "You may only access your own widgets."}), 403

    settings_payload = _get_settings_for_user(user_record)
    return jsonify(settings_payload.get("widgets", []))


@app.route("/help/faq", methods=["GET"])
def get_help_faq():
    return jsonify(_get_collection_snapshot(help_faq))


if __name__ == "__main__":
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
