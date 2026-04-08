from __future__ import annotations

import re
from datetime import datetime
from typing import Any

ALLOWED_TERMS = {"spring", "summer", "fall", "winter"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def semester_display(term: str, year: int) -> str:
    return f"{term.capitalize()} {year}"


def parse_semester(value: Any):
    if isinstance(value, dict):
        year = value.get("year")
        term = normalize_str(value.get("term")).lower()
        if not isinstance(year, int) or year < 2000 or year > 2100:
            return None, "semester.year must be an integer between 2000 and 2100."
        if term not in ALLOWED_TERMS:
            allowed_terms = ", ".join(sorted(ALLOWED_TERMS))
            return None, f"semester.term must be one of: {allowed_terms}."
        return {"year": year, "term": term, "display": semester_display(term, year)}, None

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
        return {"year": year, "term": term, "display": semester_display(term, year)}, None

    return None, "semester must be either an object {year, term} or a string like 'Fall 2026'."


def normalize_course_members(value: Any):
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

        member_id = normalize_str(entry.get("id") or entry.get("memberId") or entry.get("member_id"))
        account_email = normalize_str(entry.get("accountEmail") or entry.get("email")).lower()
        if not member_id:
            return None, None, None, "each member must include a valid id."
        if account_email and not EMAIL_RE.match(account_email):
            return None, None, None, "member email must be valid when provided."

        role = normalize_str(entry.get("role") or "student").lower()
        if role not in {"student", "instructor"}:
            return None, None, None, "member role must be 'student' or 'instructor'."
        key_limit = entry.get("key_limit")
        if key_limit is None:
            key_limit = entry.get("keyLimit")
        if key_limit is None:
            key_limit = 1
        if not isinstance(key_limit, int) or key_limit < 1:
            return None, None, None, "member key_limit must be an integer >= 1."

        normalized = {
            "id": member_id,
            "accountEmail": account_email,
            "email": account_email,
            "role": role,
            "key_limit": key_limit,
        }
        members.append(normalized)
        if role == "instructor":
            instructor_ids.append(member_id)
        else:
            student_ids.append(member_id)

    return members, instructor_ids, student_ids, None


def normalize_course_groups(value: Any):
    if value is None:
        return [], None
    if not isinstance(value, list):
        return None, "groups must be a list."

    groups = []
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, "each group must be an object."

        group_id = normalize_str(entry.get("id")) or f"group-{index}"
        name = normalize_str(entry.get("name"))
        if not name:
            return None, "each group requires a name."

        member_ids = entry.get("memberIds")
        if member_ids is None:
            member_ids = entry.get("memberEmails")
        if not isinstance(member_ids, list):
            return None, "group.memberIds must be a list."

        normalized_ids = []
        for member_id in member_ids:
            member_id_value = normalize_str(member_id)
            if not member_id_value:
                return None, "group.memberIds entries must be non-empty id strings."
            normalized_ids.append(member_id_value)

        key_limit = entry.get("key_limit")
        if key_limit is None:
            key_limit = entry.get("keyLimit")
        if key_limit is None:
            key_limit = 1
        if not isinstance(key_limit, int) or key_limit < 1:
            return None, "group key_limit must be an integer >= 1."

        groups.append({"id": group_id, "name": name, "memberIds": normalized_ids, "key_limit": key_limit})

    return groups, None


def validate_user_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    first_name = normalize_str(payload.get("first_name") or payload.get("firstName"))
    last_name = normalize_str(payload.get("last_name") or payload.get("lastName"))
    email = normalize_str(payload.get("email")).lower()
    user_id = normalize_str(payload.get("id"))
    raw_is_admin = payload.get("is_admin") if "is_admin" in payload else payload.get("isAdmin")
    if raw_is_admin is None:
        is_admin = False
    elif isinstance(raw_is_admin, bool):
        is_admin = raw_is_admin
    else:
        return None, "is_admin must be a boolean."

    raw_is_active = payload.get("is_active") if "is_active" in payload else payload.get("isActive")
    if raw_is_active is None:
        is_active = True
    elif isinstance(raw_is_active, bool):
        is_active = raw_is_active
    else:
        return None, "is_active must be a boolean."

    if not first_name:
        return None, "User first_name is required."
    if not last_name:
        return None, "User last_name is required."
    if not email or not EMAIL_RE.match(email):
        return None, "A valid user email is required."
    if not user_id:
        user_id = f"seed-{email.split('@')[0]}"

    cleaned = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "is_admin": is_admin,
        "is_active": is_active,
    }

    return cleaned, None


def validate_course_payload(payload: Any):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    name = normalize_str(payload.get("name"))
    parsed_semester, semester_error = parse_semester(payload.get("semester"))
    if semester_error:
        return None, semester_error

    if not name:
        return None, "Course name is required."

    members, member_instructors, member_students, member_error = normalize_course_members(payload.get("members"))
    if member_error:
        return None, member_error

    groups, groups_error = normalize_course_groups(payload.get("groups"))
    if groups_error:
        return None, groups_error

    instructor_ids = payload.get("instructor_ids")
    student_ids = payload.get("student_ids")

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

    cleaned = {
        "name": name,
        "instructor_ids": [v.strip() for v in instructor_ids],
        "student_ids": [v.strip() for v in student_ids],
        "semester": parsed_semester["display"],
        "semester_obj": {"year": parsed_semester["year"], "term": parsed_semester["term"]},
        "members": members,
        "groups": groups,
        "announcements": [v.strip() for v in announcements],
        "overview": normalize_str(payload.get("overview")),
        "color": normalize_str(payload.get("color")) or "#1a4a8a",
    }

    course_code = normalize_str(payload.get("code"))
    instructor_name = normalize_str(payload.get("instructor"))
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

    owner_type = normalize_str(payload.get("owner_type") or "person").lower() or "person"
    owner_id = normalize_str(payload.get("owner_id") or payload.get("u_id")).lower()
    group_id = normalize_str(payload.get("group_id")).lower() if payload.get("group_id") is not None else ""
    course_id = payload.get("course_id")
    c_id = payload.get("c_id")
    key_hash = normalize_str(payload.get("hash"))
    expire = payload.get("expire")

    if owner_type not in {"person", "group"}:
        return None, "owner_type must be either person or group."
    if not owner_id:
        return None, "owner_id is required and must be a non-empty string."
    if owner_type == "group" and not owner_id:
        owner_id = group_id
    if owner_type == "group" and not owner_id:
        return None, "owner_id is required when owner_type is group."
    if not isinstance(course_id, int):
        return None, "course_id is required and must be an integer."
    if not key_hash:
        return None, "hash is required and must be a non-empty string."
    if expire is not None:
        if not isinstance(expire, str):
            return None, "expire must be an ISO datetime string or null."
        try:
            datetime.fromisoformat(expire.replace("Z", "+00:00"))
        except ValueError:
            return None, "expire must be a valid ISO datetime string."

    return {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "u_id": owner_id if owner_type == "person" else None,
        "group_created_by": normalize_str(payload.get("group_created_by")).lower() or None,
        "course_id": course_id,
        "c_id": normalize_str(c_id) if isinstance(c_id, str) else None,
        "hash": key_hash,
        "expire": expire,
    }, None
