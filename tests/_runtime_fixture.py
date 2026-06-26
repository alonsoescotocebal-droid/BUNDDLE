"""Shared runtime fixture helpers."""

from __future__ import annotations

import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_KIN_ROOT,
    DEFAULT_PHASE01B_REBUILT_RUNTIME,
    DEFAULT_PHASE02_REBUILT_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    DEFAULT_STAT_ROOT,
)
from sll_probabilistic_pipeline.phase01a import run_phase01a
from sll_probabilistic_pipeline.phase01b import run_phase01b
from sll_probabilistic_pipeline.phase01b_join_repair import run_phase01b_join_repair
from sll_probabilistic_pipeline.phase02 import run_phase02
from sll_probabilistic_pipeline.phase03a import run_phase03a
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


@lru_cache(maxsize=1)
def build_phase01b_join_repair_runtime() -> tuple[Path, dict[str, object]]:
    phase01b_runtime, _ = build_phase01b_runtime()
    manifest = run_phase01b_join_repair(
        repo_root=REPO_ROOT,
        phase01b_runtime=phase01b_runtime,
        out_root=DEFAULT_RESULTS_ROOT,
        strict=True,
    )
    runtime_dir = Path(manifest["runtime_root"])
    return runtime_dir, manifest


@lru_cache(maxsize=1)
def build_phase02_runtime() -> tuple[Path, dict[str, object]]:
    phase01b_runtime = DEFAULT_PHASE01B_REBUILT_RUNTIME if DEFAULT_PHASE01B_REBUILT_RUNTIME.exists() else build_phase01b_runtime()[0]
    manifest = run_phase02(
        repo_root=REPO_ROOT,
        phase01b_runtime=phase01b_runtime,
        out_root=DEFAULT_RESULTS_ROOT,
        strict=True,
    )
    runtime_dir = Path(manifest["runtime_root"])
    return runtime_dir, manifest


@lru_cache(maxsize=1)
def build_phase03a_runtime() -> tuple[Path, dict[str, object]]:
    phase02_runtime = DEFAULT_PHASE02_REBUILT_RUNTIME if DEFAULT_PHASE02_REBUILT_RUNTIME.exists() else build_phase02_runtime()[0]
    manifest = run_phase03a(
        repo_root=REPO_ROOT,
        phase02_runtime=phase02_runtime,
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


def phase01b_join_repair_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase01b_join_repair_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def phase01b_join_repair_audit_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase01b_join_repair_runtime()
    return read_tsv(runtime_dir / "audit" / filename)


def phase01b_join_repair_manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_phase01b_join_repair_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def phase02_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase02_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def phase02_audit_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase02_runtime()
    return read_tsv(runtime_dir / "audit" / filename)


def phase02_manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_phase02_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def phase03a_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase03a_runtime()
    return read_tsv(runtime_dir / "data" / filename)


def phase03a_audit_rows(filename: str) -> list[dict[str, str]]:
    runtime_dir, _ = build_phase03a_runtime()
    return read_tsv(runtime_dir / "audit" / filename)


def phase03a_manifest_payload() -> dict[str, object]:
    runtime_dir, _ = build_phase03a_runtime()
    return read_json(runtime_dir / "manifest" / "runtime_manifest.json")


def clone_phase01b_runtime() -> Path:
    source_runtime = DEFAULT_PHASE01B_REBUILT_RUNTIME if DEFAULT_PHASE01B_REBUILT_RUNTIME.exists() else build_phase01b_runtime()[0]
    target = Path(tempfile.mkdtemp(prefix="phase01b_clone_", dir=_temp_parent("tests_phase02_clone")))
    shutil.copytree(source_runtime, target / source_runtime.name)
    return target / source_runtime.name


def clone_phase02_runtime() -> Path:
    source_runtime = DEFAULT_PHASE02_REBUILT_RUNTIME if DEFAULT_PHASE02_REBUILT_RUNTIME.exists() else build_phase02_runtime()[0]
    target = Path(tempfile.mkdtemp(prefix="phase02_clone_", dir=_temp_parent("tests_phase03a_clone")))
    shutil.copytree(source_runtime, target / source_runtime.name)
    return target / source_runtime.name


def cleanup_runtime() -> None:
    runtime_dir, _ = build_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)


def cleanup_phase01b_runtime() -> None:
    runtime_dir, _ = build_phase01b_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)


def cleanup_phase01b_join_repair_runtime() -> None:
    runtime_dir, _ = build_phase01b_join_repair_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)


def cleanup_phase02_runtime() -> None:
    runtime_dir, _ = build_phase02_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)


def cleanup_phase03a_runtime() -> None:
    runtime_dir, _ = build_phase03a_runtime()
    shutil.rmtree(runtime_dir, ignore_errors=True)
