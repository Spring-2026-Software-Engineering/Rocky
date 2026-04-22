from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request


def create_user(deps: dict[str, Any]):
    require_admin = deps["require_admin"]
    validate_user_payload = deps["validate_user_payload"]
    users = deps["users"]
    _bad_request = deps["_bad_request"]
    _default_user_settings = deps["_default_user_settings"]

    ok, err = require_admin()
    if not ok:
        return jsonify({"error": "Admin access is required."}), 403

    cleaned, error = validate_user_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
    cleaned["settings"] = _default_user_settings()
    cleaned["is_active"] = True
    users.insert_one(cleaned)
    return jsonify({"message": "User created"})


def get_users(deps: dict[str, Any]):
    require_admin = deps["require_admin"]
    users = deps["users"]
    _serialize_user = deps["_serialize_user"]

    ok, err = require_admin()
    if not ok:
        return jsonify({"error": "Admin access is required."}), 403

    result = [_serialize_user(user) for user in users.find()]
    return jsonify(result)


def get_user(deps: dict[str, Any], user_id: str):
    require_admin = deps["require_admin"]
    _resolve_user_record = deps["_resolve_user_record"]
    _serialize_user = deps["_serialize_user"]

    ok, err = require_admin()
    if not ok:
        return jsonify({"error": "Admin access is required."}), 403

    user = _resolve_user_record(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_serialize_user(user))


def update_user(deps: dict[str, Any], user_id: str):
    require_admin = deps["require_admin"]
    _resolve_user_record = deps["_resolve_user_record"]
    users = deps["users"]
    whitelist_users = deps["whitelist_users"]
    _bad_request = deps["_bad_request"]

    ok, err = require_admin()
    if not ok:
        return jsonify({"error": "Admin access is required."}), 403

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


def delete_user(deps: dict[str, Any], user_id: str):
    require_admin = deps["require_admin"]
    _resolve_user_record = deps["_resolve_user_record"]

    ok, err = require_admin()
    if not ok:
        return jsonify({"error": "Admin access is required."}), 403

    user = _resolve_user_record(user_id, None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"error": "User deletion is disabled. Use account activation controls."}), 405
