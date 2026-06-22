"""Shared runtime fixture helpers."""

from __future__ import annotations

import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_KIN_ROOT, DEFAULT_STAT_ROOT
from sll_probabilistic_pipeline.phase01a import run_phase01a
from sll_probabilistic_pipeline.utils import read_json, read_tsv

REPO_ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def build_runtime() -> tuple[Path, dict[str, object]]:
    temp_parent = REPO_ROOT / ".tmp_test_runtime"
    temp_parent.mkdir(parents=True, exist_ok=True)
    runtime_dir = Path(tempfile.mkdtemp(prefix="phase01a_", dir=temp_parent))
    manifest = run_phase01a(
        stat_root=DEFAULT_STAT_ROOT,
        kin_root=DEFAULT_KIN_ROOT,
        out_root=runtime_dir,
    )
    return runtime_dir, manifest


def data_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def cleanup_runtime() -> None:
    runtime_dir, _ = build_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)

