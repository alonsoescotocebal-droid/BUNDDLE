"""Shared runtime fixture helpers."""

from __future__ import annotations

import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_KIN_ROOT, DEFAULT_RESULTS_ROOT, DEFAULT_STAT_ROOT
from sll_probabilistic_pipeline.phase01a import run_phase01a
from sll_probabilistic_pipeline.phase01b import run_phase01b
from sll_probabilistic_pipeline.utils import read_json, read_tsv

REPO_ROOT = Path(__file__).resolve().parents[1]


def _temp_parent(prefix: str) -> Path:
    temp_parent = DEFAULT_RESULTS_ROOT / prefix
    temp_parent.mkdir(parents=True, exist_ok=True)
    return temp_parent


@lru_cache(maxsize=1)
def build_runtime() -> tuple[Path, dict[str, object]]:
    runtime_dir = Path(tempfile.mkdtemp(prefix="phase01a_", dir=_temp_parent("tests_phase01a")))
    manifest = run_phase01a(
        stat_root=DEFAULT_STAT_ROOT,
        kin_root=DEFAULT_KIN_ROOT,
        out_root=runtime_dir,
    )
    return runtime_dir, manifest


@lru_cache(maxsize=1)
def build_phase01b_runtime() -> tuple[Path, dict[str, object]]:
    manifest = run_phase01b(
        repo_root=REPO_ROOT,
        stat_root=DEFAULT_STAT_ROOT,
        kin_root=DEFAULT_KIN_ROOT,
        out_root=DEFAULT_RESULTS_ROOT,
        strict=True,
    )
    runtime_dir = Path(manifest["runtime_root"])
    return runtime_dir, manifest


def data_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def phase01b_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase01b_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def phase01b_audit_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase01b_runtime()
    return read_tsv(runtime_dir / "audit" / filename)


def phase01b_manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_phase01b_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def cleanup_runtime() -> None:
    runtime_dir, _ = build_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)


def cleanup_phase01b_runtime() -> None:
    runtime_dir, _ = build_phase01b_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)
