"""Load local Braintrust benchmark datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def benchmark_row_index(row: dict) -> int:
    meta = row.get("metadata") or {}
    line = meta.get("line_number")
    if isinstance(line, int):
        return line
    row_id = meta.get("benchmark_id") or row.get("id") or ""
    if isinstance(row_id, str) and row_id.startswith("fp_"):
        try:
            return int(row_id.split("_", 1)[1])
        except ValueError:
            pass
    return 0


def sort_braintrust_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=benchmark_row_index)


def load_local_dataset(path: Path, limit: int | None = None) -> list[dict]:
    text = path.read_text()
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        raw = json.loads(text)
        rows = raw if isinstance(raw, list) else raw.get("records", [])

    rows = sort_braintrust_rows(rows)
    if limit is not None:
        rows = rows[:limit]
    return rows


def load_cloud_dataset(dataset: Any, limit: int | None = None) -> Any:
    if limit is None:
        return dataset
    return sort_braintrust_rows(list(dataset))[:limit]
