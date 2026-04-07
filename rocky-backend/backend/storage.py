from __future__ import annotations

from dataclasses import dataclass

from mongita import MongitaClientDisk, MongitaClientMemory
from pymongo import MongoClient

from .config import Settings


@dataclass
class Collections:
    users: any
    whitelist_users: any
    courses: any
    api_keys: any
    api_history: any
    analytics_kpis: any
    analytics_activity: any
    widgets_default: any
    help_faq: any


def _from_db(db) -> Collections:
    return Collections(
        users=db["users"],
        whitelist_users=db["whitelist_users"],
        courses=db["courses"],
        api_keys=db["api_keys"],
        api_history=db["api_history"],
        analytics_kpis=db["analytics_kpis"],
        analytics_activity=db["analytics_activity"],
        widgets_default=db["widgets_default"],
        help_faq=db["help_faq"],
    )


def build_collections(settings: Settings) -> Collections:
    if settings.mongodb_uri and (settings.db_backend == "mongodb" or settings.app_env == "production"):
        client = MongoClient(settings.mongodb_uri)
        db = client[settings.db_name]
        return _from_db(db)

    client = MongitaClientDisk()
    db = client[settings.db_name]
    return _from_db(db)


def build_in_memory_collections(db_name: str = "rocky_test_db") -> Collections:
    client = MongitaClientMemory()
    db = client[db_name]
    return _from_db(db)
