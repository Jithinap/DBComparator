from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def rows_to_json(rows: Sequence[Sequence], cursor_description: Iterable) -> list[dict]:
    """Convert DB-API rows and cursor metadata into dictionaries."""
    columns = [column[0] for column in cursor_description]
    return [dict(zip(columns, row)) for row in rows]


def write_json(path: Path | str, rows: list[dict]) -> Path:
    output = Path(path)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, sort_keys=True)
    return output


def read_json(path: Path | str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return data


def row_diff(source_rows: Sequence[Mapping], destination_rows: Sequence[Mapping]) -> tuple[list[dict], list[dict]]:
    """Return dictionaries unique to source and destination."""
    source = {json.dumps(row, sort_keys=True, default=str): dict(row) for row in source_rows}
    destination = {json.dumps(row, sort_keys=True, default=str): dict(row) for row in destination_rows}
    source_only = [source[key] for key in source.keys() - destination.keys()]
    destination_only = [destination[key] for key in destination.keys() - source.keys()]
    return source_only, destination_only
