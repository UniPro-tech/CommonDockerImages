from __future__ import annotations

import json
from pathlib import Path

from config import STATE_DIR


def _state_path(name: str) -> Path:
    return STATE_DIR / f"{name}.json"


def load_state(name: str) -> dict:
    path = _state_path(name)

    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return {}

    return data


def save_state(
    name: str,
    data: dict,
) -> None:
    STATE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = _state_path(name)

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )

        f.write("\n")
