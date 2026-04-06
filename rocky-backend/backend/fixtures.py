from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEED_ROOT = ROOT / "seed-data"


def read_seed_json(*segments: str) -> Any:
    file_path = SEED_ROOT.joinpath(*segments)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
