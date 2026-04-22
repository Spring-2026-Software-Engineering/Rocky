from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.validation import validate_api_key_payload, validate_course_payload, validate_user_payload


def _insert_static_collection(collection, rows: list[dict[str, Any]]) -> int:
    collection.delete_many({})
    if rows:
        collection.insert_many(rows)
    return len(rows)


def seed_database(collections, payload: dict[str, Any]) -> dict[str, int]:
    summary = {
        "users_inserted": 0,
        "users_rejected": 0,
        "courses_inserted": 0,
        "courses_rejected": 0,
        "api_keys_inserted": 0,
        "api_keys_rejected": 0,
    }

    collections.users.delete_many({})
    collections.whitelist_users.delete_many({})
    collections.courses.delete_many({})
    collections.api_keys.delete_many({})
    collections.api_history.delete_many({})

    for item in payload.get("users", []):
        cleaned, error = validate_user_payload(item)
        if error:
            summary["users_rejected"] += 1
            continue
        cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
        collections.users.insert_one(cleaned)
        summary["users_inserted"] += 1

    for item in payload.get("courses", []):
        cleaned, error = validate_course_payload(item)
        if error:
            summary["courses_rejected"] += 1
            continue
        collections.courses.insert_one(cleaned)
        summary["courses_inserted"] += 1

    for item in payload.get("api_keys", []):
        cleaned, error = validate_api_key_payload(item)
        if error:
            summary["api_keys_rejected"] += 1
            continue
        cleaned["api_key_id"] = summary["api_keys_inserted"] + 1
        slot_index = cleaned.get("slot_index") if isinstance(cleaned.get("slot_index"), int) else 1
        if slot_index < 1:
            slot_index = 1
        cleaned["slot_index"] = slot_index
        cleaned["key_name"] = f"key-{slot_index}"
        provided_created = item.get("created") if isinstance(item, dict) else None
        if isinstance(provided_created, str) and provided_created.strip():
            cleaned["created"] = provided_created.strip()
        else:
            cleaned["created"] = datetime.now(timezone.utc).isoformat()
        collections.api_keys.insert_one(cleaned)
        summary["api_keys_inserted"] += 1

    return summary


def seed_static_content(collections, read_seed_json) -> dict[str, int]:
    return {
        "analytics_kpis_inserted": _insert_static_collection(collections.analytics_kpis, read_seed_json("analytics", "kpis.json")),
        "analytics_activity_inserted": _insert_static_collection(collections.analytics_activity, read_seed_json("analytics", "activity.json")),
        "widgets_default_inserted": _insert_static_collection(collections.widgets_default, read_seed_json("widgets", "widgets.json")),
        "help_faq_inserted": _insert_static_collection(collections.help_faq, read_seed_json("help", "faq.json")),
    }
