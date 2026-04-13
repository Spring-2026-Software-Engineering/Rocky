from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request


def create_course(deps: dict[str, Any]):
    require_admin = deps["require_admin"]
    validate_course_payload = deps["validate_course_payload"]
    courses = deps["courses"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]

    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    cleaned, error = validate_course_payload(request.get_json(silent=True))
    if error:
        return _bad_request(error)

    if "id" in cleaned:
        if courses.find_one({"id": cleaned["id"]}) is not None:
            return _bad_request("Course id already exists.")
    if "id" not in cleaned:
        existing_ids = [course.get("id", 0) for course in courses.find() if isinstance(course.get("id"), int)]
        cleaned["id"] = (max(existing_ids) if existing_ids else 0) + 1

    courses.insert_one(cleaned)
    return jsonify(_serialize_value(cleaned)), 201


def get_courses(deps: dict[str, Any]):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    courses = deps["courses"]
    _attach_course_key_state = deps["_attach_course_key_state"]
    _serialize_value = deps["_serialize_value"]
    filter_visible_courses = deps["filter_visible_courses"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)
    result = [_attach_course_key_state(_serialize_value(course)) for course in courses.find()]
    return jsonify(filter_visible_courses(result, requester_id or email, is_admin))


def get_course(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    courses = deps["courses"]
    get_course_record = deps["get_course_record"]
    _attach_course_key_state = deps["_attach_course_key_state"]
    _serialize_value = deps["_serialize_value"]
    filter_visible_courses = deps["filter_visible_courses"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)
    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    serialized = _attach_course_key_state(_serialize_value(course))
    visible = filter_visible_courses([serialized], requester_id or email, is_admin)
    if not visible:
        return jsonify({"error": "Not found"}), 404

    return jsonify(visible[0])


def patch_course_metadata(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    can_manage_metadata = deps["can_manage_metadata"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    users = deps["users"]
    apply_course_metadata_patch = deps["apply_course_metadata_patch"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]

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


def delete_course(deps: dict[str, Any], course_id: str):
    require_admin = deps["require_admin"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]

    ok, err = require_admin()
    if not ok:
        return jsonify(err[0]), err[1]

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    courses.delete_one({"_id": course["_id"]})
    return jsonify({"message": "Course deleted"})


def add_course_members_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    users = deps["users"]
    can_manage_people = deps["can_manage_people"]
    add_course_members = deps["add_course_members"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]

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


def remove_course_member_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    remove_course_member = deps["remove_course_member"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]

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


def create_course_group_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    create_course_group = deps["create_course_group"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]

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

    global_group_ids = {
        normalize_str(group.get("id"))
        for candidate_course in courses.find()
        for group in candidate_course.get("groups", [])
        if isinstance(group, dict)
    }
    current_course_group_ids = {
        normalize_str(group.get("id"))
        for group in course.get("groups", [])
        if isinstance(group, dict)
    }
    global_group_ids -= current_course_group_ids

    try:
        updated = create_course_group(course, data.get("name", ""), global_group_ids)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


def add_group_member_route(deps: dict[str, Any], course_id: str, group_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    add_group_member = deps["add_group_member"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]

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


def remove_group_member_route(deps: dict[str, Any], course_id: str, group_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    remove_group_member = deps["remove_group_member"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]

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


def update_member_key_limit_route(deps: dict[str, Any], course_id: str, member_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    update_course_member_key_limit = deps["update_course_member_key_limit"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    key_limit = data.get("keyLimit") if "keyLimit" in data else data.get("key_limit")
    if not isinstance(key_limit, int) or key_limit < 1:
        return _bad_request("keyLimit must be an integer >= 1.")

    try:
        updated = update_course_member_key_limit(course, member_id, key_limit)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


def update_group_key_limit_route(deps: dict[str, Any], course_id: str, group_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_manage_people = deps["can_manage_people"]
    update_course_group_key_limit = deps["update_course_group_key_limit"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not can_manage_people(course, requester_id or email, is_admin):
        return jsonify({"error": "Instructor or admin access is required."}), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    key_limit = data.get("keyLimit") if "keyLimit" in data else data.get("key_limit")
    if not isinstance(key_limit, int) or key_limit < 1:
        return _bad_request("keyLimit must be an integer >= 1.")

    try:
        updated = update_course_group_key_limit(course, group_id, key_limit)
    except ValueError as exc:
        return _bad_request(str(exc))

    courses.replace_one({"_id": course["_id"]}, updated)
    return jsonify(_serialize_value(updated))


def list_course_api_keys_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    can_request_api_key = deps["can_request_api_key"]
    _iter_course_api_keys = deps["_iter_course_api_keys"]
    _serialize_api_key_summary = deps["_serialize_api_key_summary"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity
    requester_id = _resolve_requester_user_id(email)

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not can_request_api_key(course, requester_id or email, is_admin):
        return jsonify({"error": "Course access is required."}), 403

    normalized_requester = normalize_str(requester_id or email).lower()
    requester_group_ids = {
        normalize_str(group.get("id")).lower()
        for group in course.get("groups", [])
        if isinstance(group, dict)
        and (
            normalized_requester in {normalize_str(member_id).lower() for member_id in group.get("memberIds", [])}
            or normalize_str(email).lower() in {normalize_str(member_id).lower() for member_id in group.get("memberIds", [])}
        )
    }

    result: list[dict[str, Any]] = []
    for entry in _iter_course_api_keys(course):
        owner_type = normalize_str(entry.get("owner_type")).lower() or "person"
        owner_id = normalize_str(entry.get("owner_id")).lower()
        if not is_admin:
            if owner_type == "person" and owner_id != normalized_requester:
                continue
            if owner_type == "group" and owner_id not in requester_group_ids:
                continue
        result.append(_serialize_api_key_summary(entry))

    result.sort(key=lambda item: normalize_str(item.get("key_name")))
    return jsonify(_serialize_value(result))


def _build_api_history_entry(course: dict[str, Any], requester_email: str, payload: dict[str, Any], deps: dict[str, Any]):
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    normalize_str = deps["normalize_str"]

    requester_id = _resolve_requester_user_id(requester_email)
    groups = course.get("groups") if isinstance(course.get("groups"), list) else []
    matched_group = next(
        (
            group
            for group in groups
            if isinstance(group, dict)
            and (
                requester_id in [normalize_str(member_id) for member_id in (group.get("memberIds") or group.get("memberEmails") or [])]
                or requester_email in [normalize_str(member_id).lower() for member_id in (group.get("memberIds") or group.get("memberEmails") or [])]
            )
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


def regenerate_course_api_key_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    api_keys = deps["api_keys"]
    api_history = deps["api_history"]
    can_request_api_key = deps["can_request_api_key"]
    _get_owner_key_limit = deps["_get_owner_key_limit"]
    _iter_course_api_keys = deps["_iter_course_api_keys"]
    _parse_iso_datetime = deps["_parse_iso_datetime"]
    _build_api_history_entry = deps["_build_api_history_entry"]
    regenerate_course_api_key = deps["regenerate_course_api_key"]
    _bad_request = deps["_bad_request"]
    _serialize_value = deps["_serialize_value"]
    normalize_str = deps["normalize_str"]
    API_KEY_REGENERATION_COOLDOWN = deps["API_KEY_REGENERATION_COOLDOWN"]

    identity = require_requester_identity()
    if identity[0] is None:
        return jsonify(identity[1][0]), identity[1][1]
    email, is_admin = identity

    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return _bad_request("Request body must be a JSON object.")

    course = get_course_record(courses, course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    requester_id = _resolve_requester_user_id(email)
    if not can_request_api_key(course, requester_id or email, is_admin):
        return jsonify({"error": "Course access is required."}), 403

    owner_type = normalize_str(data.get("ownerType") or data.get("owner_type")).lower() or "person"
    owner_id = normalize_str(data.get("ownerId") or data.get("owner_id") or data.get("groupId") or data.get("group_id"))

    normalized_requester = normalize_str(requester_id or email).lower()

    if not is_admin:
        if owner_type == "group":
            target_group_id = owner_id
            target_group = next(
                (
                    group
                    for group in course.get("groups", [])
                    if isinstance(group, dict) and normalize_str(group.get("id")).lower() == normalize_str(target_group_id).lower()
                ),
                None,
            )
            if target_group is None:
                return _bad_request("groupId is required for group keys.")
            is_group_member = normalized_requester in {
                normalize_str(member_id).lower()
                for member_id in target_group.get("memberIds", [])
            }
            if not is_group_member:
                return jsonify({"error": "Group membership is required."}), 403
            owner_type = "group"
            owner_id = normalize_str(target_group.get("id"))
        else:
            owner_type = "person"
            owner_id = normalized_requester
    elif owner_type == "group" and not owner_id:
        return _bad_request("groupId is required for group keys.")

    owner_id = normalize_str(owner_id or normalized_requester).lower()
    key_name = normalize_str(data.get("keyName") or data.get("key_name") or "key-1")[:64].strip() or "key-1"

    owner_key_limit = _get_owner_key_limit(course, owner_type, owner_id)
    owner_keys = [
        entry
        for entry in _iter_course_api_keys(course)
        if normalize_str(entry.get("owner_type")).lower() == owner_type
        and normalize_str(entry.get("owner_id")).lower() == owner_id
    ]
    target_key = next(
        (entry for entry in owner_keys if normalize_str(entry.get("key_name")) == key_name),
        None,
    )
    if target_key is None and len(owner_keys) >= owner_key_limit:
        return _bad_request(f"Key limit reached for this owner ({owner_key_limit}).")

    target_key_created_at = _parse_iso_datetime(target_key.get("created")) if isinstance(target_key, dict) else None
    if target_key_created_at is not None and datetime.now(timezone.utc) - target_key_created_at < API_KEY_REGENERATION_COOLDOWN:
        remaining = API_KEY_REGENERATION_COOLDOWN - (datetime.now(timezone.utc) - target_key_created_at)
        minutes = max(1, int(remaining.total_seconds() // 60) + (1 if remaining.total_seconds() % 60 else 0))
        return jsonify({"error": f"Please wait {minutes} minute(s) before generating another key."}), 429

    ownership = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "key_name": key_name,
    }

    try:
        key_doc = regenerate_course_api_key(course, api_keys, requester_id or email, ownership)
    except ValueError as exc:
        return _bad_request(str(exc))

    history_doc = _build_api_history_entry(
        course,
        email,
        {
            "eventType": "generate-key",
            "groupId": owner_id if owner_type == "group" else "",
            "groupName": normalize_str(data.get("groupName") or data.get("group_name")),
            "meta": {
                "path": request.path,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "key_name": key_name,
            },
        },
        deps,
    )
    api_history.insert_one(history_doc)

    return jsonify(_serialize_value(key_doc))


def delete_course_api_key_route(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    api_keys = deps["api_keys"]
    can_manage_api_keys = deps["can_manage_api_keys"]
    delete_course_api_keys = deps["delete_course_api_keys"]
    _bad_request = deps["_bad_request"]

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


def append_course_api_history(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    api_history = deps["api_history"]
    filter_visible_courses = deps["filter_visible_courses"]
    _serialize_value = deps["_serialize_value"]
    _build_api_history_entry = deps["_build_api_history_entry"]
    _bad_request = deps["_bad_request"]

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

    history_doc = _build_api_history_entry(course, email, payload, deps)
    api_history.insert_one(history_doc)
    return jsonify(_serialize_value(history_doc)), 201


def get_course_api_history(deps: dict[str, Any], course_id: str):
    require_requester_identity = deps["require_requester_identity"]
    _resolve_requester_user_id = deps["_resolve_requester_user_id"]
    get_course_record = deps["get_course_record"]
    courses = deps["courses"]
    api_history = deps["api_history"]
    filter_visible_courses = deps["filter_visible_courses"]
    _serialize_value = deps["_serialize_value"]
    can_manage_people = deps["can_manage_people"]
    normalize_str = deps["normalize_str"]

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
