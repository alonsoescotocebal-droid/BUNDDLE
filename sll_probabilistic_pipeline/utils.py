"""Stdlib utility helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader]


def read_tsv_with_header(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


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


def write_json_list(path: Path, payload: list[dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def stable_trace_id(*parts: object) -> str:
    payload = "|".join(stringify(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def normcase_path(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).resolve(strict=False)))


def is_same_or_within(path: str | Path, parent: str | Path) -> bool:
    path_norm = normcase_path(path)
    parent_norm = normcase_path(parent)
    try:
        return os.path.commonpath([path_norm, parent_norm]) == parent_norm
    except ValueError:
        return False


def path_snapshot(
    root: Path,
    *,
    include_exts: tuple[str, ...] = (".tsv", ".json", ".md"),
    include_dir_prefixes: tuple[str, ...] = (".tmp_", "runtime_", "SLL_PHASE01B_", "SLL_PHASE02_", "SLL_PHASE03_"),
    include_dir_names: tuple[str, ...] = ("audit", "manifest", "logs", "report"),
) -> set[str]:
    snapshot: set[str] = set()
    root_path = Path(root)
    for current_root, dir_names, file_names in os.walk(root_path, onerror=lambda _error: None):
        current_root_path = Path(current_root)
        try:
            rel_root = current_root_path.relative_to(root_path)
        except ValueError:
            continue
        rel_root_text = str(rel_root).replace("\\", "/")
        if rel_root_text != "." and (
            current_root_path.name in include_dir_names
            or any(current_root_path.name.startswith(prefix) for prefix in include_dir_prefixes)
        ):
            snapshot.add(rel_root_text)
        for name in dir_names:
            if name in include_dir_names or any(name.startswith(prefix) for prefix in include_dir_prefixes):
                rel_text = str((rel_root / name)).replace("\\", "/")
                snapshot.add(rel_text)
        for name in file_names:
            rel_text = str((rel_root / name)).replace("\\", "/")
            suffix = Path(name).suffix.lower()
            if suffix in include_exts or any(name.startswith(prefix) for prefix in include_dir_prefixes):
                snapshot.add(rel_text)
    return snapshot


def fieldnames_from_rows(rows: list[dict[str, object]], preferred_order: list[str] | tuple[str, ...]) -> list[str]:
    names: list[str] = list(preferred_order)
    seen = set(names)
    for row in rows:
        for key in row.keys():
            if key in seen:
                continue
            seen.add(key)
            names.append(key)
    return names
