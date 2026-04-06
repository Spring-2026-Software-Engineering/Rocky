from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from backend.validation import EMAIL_RE, normalize_str, parse_semester

GROUP_ID_RE = re.compile(r"[^a-z0-9]+")


def course_matches_identifier(course: dict[str, Any], identifier: str) -> bool:
    if str(course.get("id")) == identifier:
        return True

    course_object_id = course.get("_id")
    return str(course_object_id) == identifier


def get_course_record(courses_collection, course_id: str):
    try:
        course = courses_collection.find_one({"_id": ObjectId(course_id)})
        if course:
            return course
    except (InvalidId, TypeError):
        pass

    for candidate in courses_collection.find():
        if course_matches_identifier(candidate, course_id):
            return candidate

    return None


def _set_course_member_lists(course: dict[str, Any]) -> None:
    members = course.get("members", []) if isinstance(course.get("members"), list) else []
    instructor_ids = []
    student_ids = []
    normalized_members = []

    for member in members:
        if not isinstance(member, dict):
            continue

        email = normalize_str(member.get("accountEmail") or member.get("email")).lower()
        name = normalize_str(member.get("name")) or "Unknown User"
        role = normalize_str(member.get("role") or "student").lower()
        if not email or not EMAIL_RE.match(email):
            continue
        if role not in {"student", "instructor"}:
            role = "student"

        normalized = {
            "accountEmail": email,
            "email": email,
            "name": name,
            "role": role,
        }
        normalized_members.append(normalized)
        if role == "instructor":
            instructor_ids.append(email)
        else:
            student_ids.append(email)

    course["members"] = normalized_members
    course["instructor_ids"] = instructor_ids
    course["student_ids"] = student_ids
    if instructor_ids:
        first_instructor = next((member for member in normalized_members if member["role"] == "instructor"), None)
        if first_instructor:
            course["instructor"] = first_instructor["name"]


def _lookup_user(users_collection, email: str):
    return users_collection.find_one({"email": email.lower()})


def _is_course_admin(role: str) -> bool:
    return role == "admin"


def _is_course_instructor(course: dict[str, Any], email: str) -> bool:
    normalized_email = email.lower()
    for member in course.get("members", []):
        if not isinstance(member, dict):
            continue
        member_email = normalize_str(member.get("accountEmail") or member.get("email")).lower()
        if member_email == normalized_email and normalize_str(member.get("role")).lower() == "instructor":
            return True
    return False


def can_manage_people(course: dict[str, Any], requester_email: str, requester_role: str) -> bool:
    return _is_course_admin(requester_role) or (requester_role == "instructor" and _is_course_instructor(course, requester_email))


def can_manage_metadata(requester_role: str) -> bool:
    return _is_course_admin(requester_role)


def can_manage_api_keys(requester_role: str) -> bool:
    return _is_course_admin(requester_role)


def course_is_visible_to_requester(course: dict[str, Any], requester_email: str, requester_role: str) -> bool:
    if _is_course_admin(requester_role):
        return True
    return _is_course_instructor(course, requester_email) or any(
        normalize_str(member.get("accountEmail") or member.get("email")).lower() == requester_email.lower()
        for member in course.get("members", [])
        if isinstance(member, dict)
    )


def filter_visible_courses(courses: list[dict[str, Any]], requester_email: str | None, requester_role: str | None) -> list[dict[str, Any]]:
    if requester_role == "admin":
        return courses
    if not requester_email:
        return []
    return [course for course in courses if course_is_visible_to_requester(course, requester_email, requester_role or "")]


def apply_course_metadata_patch(course: dict[str, Any], users_collection, payload: dict[str, Any]) -> dict[str, Any]:
    name = payload.get("name")
    code = payload.get("code")
    semester = payload.get("semester")
    instructor_email = normalize_str(payload.get("instructorEmail")).lower()

    if name is not None:
        course["name"] = normalize_str(name) or course.get("name", "Untitled Course")
    if code is not None:
        course["code"] = normalize_str(code) or course.get("code", "TBD 0000")
    if semester is not None:
        parsed_semester, semester_error = parse_semester(semester)
        if semester_error:
            raise ValueError(semester_error)
        course["semester"] = parsed_semester["display"]
        course["semester_obj"] = {"year": parsed_semester["year"], "term": parsed_semester["term"]}

    if instructor_email is not None:
        if instructor_email:
            if not EMAIL_RE.match(instructor_email):
                raise ValueError("instructorEmail must be a valid email.")
            user = _lookup_user(users_collection, instructor_email)
            if not user:
                raise ValueError("Instructor email must match an existing user.")
            instructor_name = normalize_str(user.get("name")) or "Unknown Instructor"
            course["instructor"] = instructor_name
            course["members"] = [
                member
                for member in course.get("members", [])
                if not (isinstance(member, dict) and normalize_str(member.get("role")).lower() == "instructor")
            ]
            course.setdefault("members", [])
            course["members"].insert(
                0,
                {
                    "accountEmail": instructor_email,
                    "email": instructor_email,
                    "name": instructor_name,
                    "role": "instructor",
                },
            )
        else:
            course["members"] = [
                member
                for member in course.get("members", [])
                if not (isinstance(member, dict) and normalize_str(member.get("role")).lower() == "instructor")
            ]
            course["instructor"] = "Unknown Instructor"

    _set_course_member_lists(course)
    return course


def add_course_members(course: dict[str, Any], users_collection, payload: Any, requester_role: str) -> dict[str, Any]:
    if isinstance(payload, dict) and "members" in payload:
        members_payload = payload.get("members")
    else:
        members_payload = payload

    if isinstance(members_payload, dict):
        members_payload = [members_payload]

    if not isinstance(members_payload, list):
        raise ValueError("members must be a list or member object.")

    existing_members = {
        normalize_str(member.get("accountEmail") or member.get("email")).lower(): member
        for member in course.get("members", [])
        if isinstance(member, dict)
    }

    for entry in members_payload:
        if not isinstance(entry, dict):
            raise ValueError("each member must be an object.")

        email = normalize_str(entry.get("email") or entry.get("accountEmail")).lower()
        role = normalize_str(entry.get("role") or "student").lower()
        if not email or not EMAIL_RE.match(email):
            raise ValueError("each member requires a valid email.")
        if role not in {"student", "instructor"}:
            raise ValueError("member role must be student or instructor.")
        if role == "instructor" and requester_role != "admin":
            raise ValueError("Only admins can add instructor members.")

        user = _lookup_user(users_collection, email)
        if not user:
            raise ValueError(f"Unknown user: {email}")

        name = normalize_str(user.get("name")) or "Unknown User"
        existing_members[email] = {
            "accountEmail": email,
            "email": email,
            "name": name,
            "role": role,
        }

    course["members"] = list(existing_members.values())
    _set_course_member_lists(course)
    return course


def remove_course_member(course: dict[str, Any], email: str, requester_role: str) -> dict[str, Any]:
    normalized_email = normalize_str(email).lower()
    if not normalized_email or not EMAIL_RE.match(normalized_email):
        raise ValueError("email must be valid.")

    current_member = next(
        (
            member
            for member in course.get("members", [])
            if isinstance(member, dict) and normalize_str(member.get("accountEmail") or member.get("email")).lower() == normalized_email
        ),
        None,
    )
    if current_member and normalize_str(current_member.get("role")).lower() == "instructor" and requester_role != "admin":
        raise ValueError("Only admins can remove instructor members.")

    course["members"] = [
        member
        for member in course.get("members", [])
        if not (isinstance(member, dict) and normalize_str(member.get("accountEmail") or member.get("email")).lower() == normalized_email)
    ]

    for group in course.get("groups", []):
        if not isinstance(group, dict):
            continue
        member_emails = [
            member_email
            for member_email in group.get("memberEmails", [])
            if normalize_str(member_email).lower() != normalized_email
        ]
        group["memberEmails"] = member_emails

    _set_course_member_lists(course)
    return course


def create_course_group(course: dict[str, Any], name: str) -> dict[str, Any]:
    group_name = normalize_str(name)
    if not group_name:
        raise ValueError("group name is required.")

    safe_slug = GROUP_ID_RE.sub("-", group_name.lower()).strip("-") or "group"
    existing_ids = {
        normalize_str(group.get("id"))
        for group in course.get("groups", [])
        if isinstance(group, dict)
    }
    suffix = 1
    group_id = f"{safe_slug}-{suffix}"
    while group_id in existing_ids:
        suffix += 1
        group_id = f"{safe_slug}-{suffix}"

    course.setdefault("groups", [])
    course["groups"].append({"id": group_id, "name": group_name, "memberEmails": []})
    return course


def add_group_member(course: dict[str, Any], group_id: str, email: str) -> dict[str, Any]:
    normalized_group_id = normalize_str(group_id)
    normalized_email = normalize_str(email).lower()
    if not normalized_group_id:
        raise ValueError("groupId is required.")
    if not normalized_email or not EMAIL_RE.match(normalized_email):
        raise ValueError("email must be valid.")

    group = next((group for group in course.get("groups", []) if isinstance(group, dict) and normalize_str(group.get("id")) == normalized_group_id), None)
    if not group:
        raise ValueError("Group not found.")

    member_emails = [normalize_str(member_email).lower() for member_email in group.get("memberEmails", [])]
    if normalized_email not in member_emails:
        member_emails.append(normalized_email)
    group["memberEmails"] = member_emails
    return course


def remove_group_member(course: dict[str, Any], group_id: str, email: str) -> dict[str, Any]:
    normalized_group_id = normalize_str(group_id)
    normalized_email = normalize_str(email).lower()
    if not normalized_group_id:
        raise ValueError("groupId is required.")
    if not normalized_email or not EMAIL_RE.match(normalized_email):
        raise ValueError("email must be valid.")

    group = next((group for group in course.get("groups", []) if isinstance(group, dict) and normalize_str(group.get("id")) == normalized_group_id), None)
    if not group:
        raise ValueError("Group not found.")

    group["memberEmails"] = [
        member_email
        for member_email in group.get("memberEmails", [])
        if normalize_str(member_email).lower() != normalized_email
    ]
    return course


def regenerate_course_api_key(course: dict[str, Any], api_keys_collection, requester_email: str) -> dict[str, Any]:
    course_code = normalize_str(course.get("code"))
    if not course_code:
        raise ValueError("Course code is required for API key management.")

    api_keys_collection.delete_many({"c_id": course_code})
    instructor_email = next(
        (
            normalize_str(member.get("accountEmail") or member.get("email")).lower()
            for member in course.get("members", [])
            if isinstance(member, dict) and normalize_str(member.get("role")).lower() == "instructor"
        ),
        requester_email.lower(),
    )

    key_doc = {
        "u_id": instructor_email,
        "c_id": course_code,
        "expire": None,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    api_keys_collection.insert_one(key_doc)
    return key_doc


def delete_course_api_keys(course: dict[str, Any], api_keys_collection) -> int:
    course_code = normalize_str(course.get("code"))
    if not course_code:
        raise ValueError("Course code is required for API key management.")

    result = api_keys_collection.delete_many({"c_id": course_code})
    return int(getattr(result, "deleted_count", 0))
