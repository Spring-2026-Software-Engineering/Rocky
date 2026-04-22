from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import jsonify, render_template


def _redact_inspector_value(value: Any):
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key == "html" or normalized_key.endswith("_html"):
                continue
            redacted[key] = _redact_inspector_value(item)
        return redacted
    if isinstance(value, list):
        return [_redact_inspector_value(item) for item in value]
    return value


def health_check(deps: dict[str, Any]):
    settings = deps["settings"]
    return jsonify({"ok": True, "env": settings.app_env})


def index_page(deps: dict[str, Any]):
    settings = deps["settings"]
    _get_collection_snapshot = deps["_get_collection_snapshot"]
    users = deps["users"]
    whitelist_users = deps["whitelist_users"]
    courses = deps["courses"]
    api_keys = deps["api_keys"]
    api_history = deps["api_history"]

    if settings.app_env == "production" and not settings.enable_db_inspector:
        return jsonify({"error": "Not found"}), 404

    collections_snapshot = {
        "users": {
            "docs": _redact_inspector_value(_get_collection_snapshot(users)),
            "description": "Canonical user records; each user document owns its settings.",
        },
        "whitelist_users": {
            "docs": _redact_inspector_value(_get_collection_snapshot(whitelist_users)),
            "description": "Approved non-@kent.edu addresses for Microsoft OAuth login.",
        },
        "courses": {
            "docs": _redact_inspector_value(_get_collection_snapshot(courses)),
            "description": "Course records and memberships.",
        },
        "api_keys": {
            "docs": _redact_inspector_value(_get_collection_snapshot(api_keys)),
            "description": "Issued API keys.",
        },
        "api_history": {
            "docs": _redact_inspector_value(_get_collection_snapshot(api_history)),
            "description": "Per-course API request history.",
        },
    }
    return render_template(
        "index.html",
        generated_at=datetime.now(timezone.utc).isoformat(),
        collections=collections_snapshot,
    )


def get_analytics_kpis(deps: dict[str, Any]):
    require_admin = deps["require_admin"]
    _get_collection_snapshot = deps["_get_collection_snapshot"]
    analytics_kpis = deps["analytics_kpis"]

    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    return jsonify(_get_collection_snapshot(analytics_kpis))


def get_analytics_activity(deps: dict[str, Any]):
    require_admin = deps["require_admin"]
    _get_collection_snapshot = deps["_get_collection_snapshot"]
    analytics_activity = deps["analytics_activity"]

    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    return jsonify(_get_collection_snapshot(analytics_activity))


def get_default_widgets(deps: dict[str, Any]):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    _resolve_user_record = deps["_resolve_user_record"]
    _can_access_user_record = deps["_can_access_user_record"]
    _get_settings_for_user = deps["_get_settings_for_user"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]

    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)
    user_record = _resolve_user_record(requester_id, email)
    if not user_record:
        return jsonify({"error": "User not found"}), 404

    if not _can_access_user_record(email, is_admin, user_record):
        return jsonify({"error": "You may only access your own settings."}), 403

    settings_payload = _get_settings_for_user(user_record)
    return jsonify(settings_payload.get("widgets", []))


def get_help_faq(deps: dict[str, Any]):
    _get_collection_snapshot = deps["_get_collection_snapshot"]
    help_faq = deps["help_faq"]
    return jsonify(_get_collection_snapshot(help_faq))
