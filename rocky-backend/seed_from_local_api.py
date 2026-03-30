from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from mongita import MongitaClientMemory

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "rocky-backend"
FIXTURE_PATH = ROOT / "run-test" / "backend" / "seed_data.json"
USERS_FILE = ROOT / "rocky-interface" / "static" / "local-api" / "account" / "users.json"
COURSES_FILE = ROOT / "rocky-interface" / "static" / "local-api" / "courses" / "courses.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_semester(raw: str) -> tuple[int, str]:
    value = (raw or "").strip()
    if not value:
        return datetime.now(timezone.utc).year, "spring"

    parts = value.split()
    if len(parts) != 2:
        return datetime.now(timezone.utc).year, "spring"

    term = parts[0].strip().lower()
    try:
        year = int(parts[1].strip())
    except ValueError:
        year = datetime.now(timezone.utc).year

    if term not in {"spring", "summer", "fall", "winter"}:
        term = "spring"

    return year, term


def seed_from_local_api() -> dict[str, int]:
    # Ensure Mongita database path matches backend runtime behavior.
    os.chdir(BACKEND_DIR)

    raw_users = _load_json(USERS_FILE)
    raw_courses = _load_json(COURSES_FILE)

    main.users.delete_many({})
    main.courses.delete_many({})
    main.api_keys.delete_many({})

    users_inserted = 0
    courses_inserted = 0
    api_keys_inserted = 0

    for raw in raw_users:
        email = (raw.get("email") or "").strip().lower()
        if not email:
            continue

        role = (raw.get("role") or "client").strip().lower()
        if role not in {"admin", "client", "student", "instructor"}:
            role = "client"

        user_doc = {
            "name": (raw.get("name") or "Unknown User").strip(),
            "email": email,
            "flash_id": f"seed-{email.split('@')[0]}",
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        main.users.insert_one(user_doc)
        users_inserted += 1

    for index, raw in enumerate(raw_courses, start=1):
        semester_raw = (raw.get("semester") or "Spring 2026").strip()
        year, term = _parse_semester(semester_raw)

        members = raw.get("members") if isinstance(raw.get("members"), list) else []
        instructor_ids: list[str] = []
        student_ids: list[str] = []
        normalized_members = []

        for member in members:
            account_email = (member.get("accountEmail") or member.get("email") or "").strip().lower()
            if not account_email:
                continue

            role = (member.get("role") or "student").strip().lower()
            if role != "instructor":
                role = "student"

            normalized_members.append(
                {
                    "accountEmail": account_email,
                    "email": account_email,
                    "role": role,
                }
            )

            if role == "instructor":
                instructor_ids.append(account_email)
            else:
                student_ids.append(account_email)

        course_doc = {
            # Fields consumed by frontend
            "id": raw.get("id") if isinstance(raw.get("id"), int) else index,
            "code": (raw.get("code") or f"TBD {1000 + index}").strip(),
            "name": (raw.get("name") or "Untitled Course").strip(),
            "instructor": (raw.get("instructor") or "Unknown Instructor").strip(),
            "semester": semester_raw,
            "color": (raw.get("color") or "#1a4a8a").strip(),
            "overview": (raw.get("overview") or "").strip(),
            "announcements": raw.get("announcements") if isinstance(raw.get("announcements"), list) else [],
            "members": normalized_members,
            "groups": raw.get("groups") if isinstance(raw.get("groups"), list) else [],
            # Fields expected by backend create/update shape
            "instructor_ids": instructor_ids,
            "student_ids": student_ids,
            "semester_obj": {"year": year, "term": term},
        }

        main.courses.insert_one(course_doc)
        courses_inserted += 1

        if instructor_ids:
            key_doc = {
                "u_id": instructor_ids[0],
                "c_id": course_doc["code"],
                "expire": None,
                "created": datetime.now(timezone.utc).isoformat(),
            }
            main.api_keys.insert_one(key_doc)
            api_keys_inserted += 1

    return {
        "users_inserted": users_inserted,
        "courses_inserted": courses_inserted,
        "api_keys_inserted": api_keys_inserted,
    }


def use_in_memory_db() -> None:
    """Route backend collections to an isolated in-memory database for tests."""
    client = MongitaClientMemory()
    test_db = client["rocky_test_db"]
    main.users = test_db["users"]
    main.courses = test_db["courses"]
    main.api_keys = test_db["api_keys"]


def load_seed_fixture(path: Path = FIXTURE_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def seed_backend_from_fixture(path: Path = FIXTURE_PATH) -> dict[str, int]:
    payload = load_seed_fixture(path)
    return main.seed_database(payload)


if __name__ == "__main__":
    summary = seed_from_local_api()
    print(f"[seed] Seeded backend from local-api fixture data: {summary}")
