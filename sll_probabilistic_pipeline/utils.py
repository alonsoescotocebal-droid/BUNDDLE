"""Stdlib utility helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader]


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, object]],
    fieldnames: list[str],
) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: stringify(row.get(name, "")) for name in fieldnames})


def read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, object]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def as_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def canonical_bool_text(value: bool | None) -> str:
    if value is None:
        return ""
    return yes_no(value)


def normalize_label(label: str) -> str:
    return "".join(ch for ch in label.lower().strip() if ch.isalnum())


def unique_by(rows: Iterable[dict[str, object]], keys: tuple[str, ...]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    result: list[dict[str, object]] = []
    for row in rows:
        marker = tuple(row.get(key) for key in keys)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(row)
    return result

