import json
import sys
from pathlib import Path

from mongita import MongitaClientMemory

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "run-test" / "backend" / "seed_data.json"
BACKEND_PATH = ROOT / "rocky-backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

import main


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
    use_in_memory_db()
    summary = seed_backend_from_fixture()
    print("Seed summary:", summary)
