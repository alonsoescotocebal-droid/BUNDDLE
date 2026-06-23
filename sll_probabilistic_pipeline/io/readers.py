"""Input reading helpers for Phase 01B."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..utils import read_json, read_tsv_with_header, sha256_file


@dataclass(frozen=True)
class LoadedSurface:
    path: Path
    source_layer: str
    source_surface: str
    branch_or_run: str
    format: str
    rows: list[dict[str, str]]
    header: list[str]
    json_payload: dict[str, object] | None

    @property
    def row_count(self) -> int:
        if self.format == "json":
            return 1
        return len(self.rows)

    @property
    def column_count(self) -> int:
        if self.format == "json":
            return len(self.header)
        return len(self.header)


def load_tsv_surface(
    path: Path,
    *,
    source_layer: str,
    source_surface: str,
    branch_or_run: str,
) -> LoadedSurface:
    rows, header = read_tsv_with_header(path)
    return LoadedSurface(
        path=path,
        source_layer=source_layer,
        source_surface=source_surface,
        branch_or_run=branch_or_run,
        format="tsv",
        rows=rows,
        header=header,
        json_payload=None,
    )


def load_json_surface(
    path: Path,
    *,
    source_layer: str,
    source_surface: str,
    branch_or_run: str,
) -> LoadedSurface:
    payload = read_json(path)
    return LoadedSurface(
        path=path,
        source_layer=source_layer,
        source_surface=source_surface,
        branch_or_run=branch_or_run,
        format="json",
        rows=[],
        header=sorted(payload.keys()),
        json_payload=payload,
    )


def input_file_hash_row(surface: LoadedSurface) -> dict[str, object]:
    return {
        "source_layer": surface.source_layer,
        "branch_or_run": surface.branch_or_run,
        "source_surface": surface.source_surface,
        "source_path": str(surface.path),
        "sha256": sha256_file(surface.path),
    }


def schema_inventory_row(surface: LoadedSurface) -> dict[str, object]:
    return {
        "source_layer": surface.source_layer,
        "branch_or_run": surface.branch_or_run,
        "source_surface": surface.source_surface,
        "source_path": str(surface.path),
        "format": surface.format,
        "row_count": surface.row_count,
        "column_count": surface.column_count,
        "columns_joined": ";".join(surface.header),
    }
