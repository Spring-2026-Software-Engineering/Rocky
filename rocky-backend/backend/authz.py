from __future__ import annotations

from typing import Any

from flask import request


def get_requester() -> tuple[str | None, str | None]:
    email = request.headers.get("X-Rocky-User-Email", "").strip().lower() or None
    role = request.headers.get("X-Rocky-User-Role", "").strip().lower() or None
    return email, role


def require_admin() -> tuple[bool, tuple[dict[str, Any], int] | None]:
    _, role = get_requester()
    if role != "admin":
        return False, ({"error": "Admin role is required."}, 403)
    return True, None


def require_requester_identity() -> tuple[str, str] | tuple[None, tuple[dict[str, Any], int]]:
    email, role = get_requester()
    if not email or not role:
        return None, ({"error": "Authentication headers are required."}, 401)
    return email, role


def authorize_scope(email: str, role: str, scope: str, user_id: str | None = None) -> tuple[bool, tuple[dict[str, Any], int] | None]:
    if role == "admin":
        return True, None

    allowed_scopes = {f"email:{email}"}
    if user_id:
        allowed_scopes.add(f"id:{user_id.strip().lower()}")

    if scope not in allowed_scopes:
        return False, ({"error": "You may only access your own settings."}, 403)

    return True, None


def filter_courses_for_requester(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    email, role = get_requester()
    if role == "admin":
        return courses

    if not email:
        return []

    filtered = []
    for course in courses:
        member_emails = {
            (member.get("accountEmail") or member.get("email") or "").strip().lower()
            for member in course.get("members", [])
            if isinstance(member, dict)
        }
        if email in member_emails:
            filtered.append(course)
    return filtered
