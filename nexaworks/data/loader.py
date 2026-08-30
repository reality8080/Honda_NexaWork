from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_DATASET_CANDIDATES = (
    Path("data/candidate_dataset.json"),
    Path("candidate_dataset.json"),
)


def find_dataset_path(path: str | Path | None = None) -> Path:
    if path is not None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {p}")
        return p
    for candidate in DEFAULT_DATASET_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "candidate_dataset.json not found. Put it under data/ or pass an explicit path."
    )


def load_dataset(path: str | Path | None = None) -> dict[str, Any]:
    p = find_dataset_path(path)
    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise TypeError("Dataset root must be a JSON object")
    return raw
