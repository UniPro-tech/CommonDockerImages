from __future__ import annotations

import json
from pathlib import Path

from config import STATE_DIR


def state_path(image_name: str) -> Path:
    return STATE_DIR / f"{image_name}.json"


def load_state(image_name: str) -> dict:
    path = state_path(image_name)

    if not path.exists():
        return {}

    with path.open() as f:
        return json.load(f)


def save_state(image_name: str, state: dict) -> None:
    path = state_path(image_name)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("w") as f:
        json.dump(
            state,
            f,
            indent=2,
            sort_keys=True,
        )
        f.write("\n")
