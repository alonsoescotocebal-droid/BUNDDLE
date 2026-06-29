"""Path resolution for the pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import (
    DEFAULT_RESULTS_ROOT,
    KINETIC_REAL_ONLY_OPTIONAL_SURFACES,
    KINETIC_REAL_ONLY_REQUIRED_SURFACES,
    PHASE01B_REPO_OUTPUT_REJECTION_CODE,
    PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX,
    PHASE01B_RUNTIME_PREFIX,
    PHASE01B_REQUIRED_OUTPUTS,
    PHASE02_REPO_OUTPUT_REJECTION_CODE,
    PHASE02_RUNTIME_PREFIX,
    PHASE02_REQUIRED_INPUTS,
    PHASE03A_REPO_OUTPUT_REJECTION_CODE,
    PHASE03A_RUNTIME_PREFIX,
    PHASE03A_REQUIRED_INPUTS,
    PHASE03B1_REPO_OUTPUT_REJECTION_CODE,
    PHASE03B1_RUNTIME_PREFIX,
    SCENARIO_ALIASES,
    STAT_RUN_REQUIRED_SURFACES,
)
from .utils import is_same_or_within, utc_stamp


class Phase01BPathError(RuntimeError):
    """Phase 01B path validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class Phase02PathError(RuntimeError):
    """Phase 02 path validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class Phase03APathError(RuntimeError):
    """Phase 03A path validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class Phase03B1PathError(RuntimeError):
    """Phase 03B1 path validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ResolvedPhase01APaths:
    stat_root: Path
    kin_root: Path
    stat_identity_run: Path
    stat_analysis_view_observed: Path
    stat_csv_contract_normalized: Path
    stat_availability_matrix: Path
    stat_label_mapping_audit: Path
    kin_real_only_root: Path
    kin_growth_source_audit: Path
    kin_metabolite_handoff: Path
    kin_report_contract_summary: Path


@dataclass(frozen=True)
class StatRunSurfaceSet:
    run_folder: Path
    run_max_lag: int
    effects: Path
    network_partialcorr: Path
    interdependence_windows: Path
    snapshots: Path
    window_deltas: Path
    pcmci_dense_replicate_input: Path
    dense_series_interpolated: Path
    analysis_view_observed: Path
    pcmci_qc: Path
    partialcorr_qc: Path
    pcmci_dense_qc: Path
    postrun_statistical_audits: Path
    series_index: Path
    availability_matrix: Path
    schema_check: Path
    run_manifest: Path


@dataclass(frozen=True)
class ResolvedPhase01BPaths:
    repo_root: Path
    stat_root: Path
    kin_root: Path
    requested_out_root: Path
    allowed_results_root: Path
    runtime_root: Path
    stat_runs: dict[int, StatRunSurfaceSet]
    kin_real_only_root: Path
    kin_real_plus_root: Path
    kin_report_output_catalog: Path
    kin_report_contract_summary: Path
    kin_report_contract_metrics: Path


@dataclass(frozen=True)
class ResolvedPhase01BJoinRepairPaths:
    repo_root: Path
    phase01b_runtime: Path
    requested_out_root: Path
    allowed_results_root: Path
    runtime_root: Path
    input_manifest: Path
    input_validation_summary: Path
    input_join_audit: Path


@dataclass(frozen=True)
class ResolvedPhase02Paths:
    repo_root: Path
    phase01b_runtime: Path
    requested_out_root: Path
    allowed_results_root: Path
    runtime_root: Path
    input_manifest: Path
    input_validation_summary: Path


@dataclass(frozen=True)
class ResolvedPhase03APaths:
    repo_root: Path
    phase02_runtime: Path
    requested_out_root: Path
    allowed_results_root: Path
    runtime_root: Path
    input_manifest: Path
    input_validation_summary: Path


@dataclass(frozen=True)
class ResolvedPhase03B1Paths:
    repo_root: Path
    phase03a_runtime: Path
    requested_out_root: Path
    allowed_results_root: Path
    runtime_root: Path
    input_manifest: Path
    input_validation_summary: Path


LAG_FOLDER_RE = re.compile(r"^SLL_REAL_PCMCI_LAG(?P<lag>\d{2})_")


def canonicalize_scenario(value: str) -> str:
    return SCENARIO_ALIASES.get(value, value)


def classify_condition_role(condition_id: str, paired_condition_id: str, family: str = "") -> str:
    if family == "Control":
        return "control"
    if condition_id.endswith("_Control"):
        return "control"
    if paired_condition_id:
        return "test"
    if family:
        return "test"
    return "test"


def _surface_path(run_folder: Path, relative_path: str) -> Path:
    return run_folder / Path(relative_path.replace("/", "\\"))


def resolve_phase01a_paths(stat_root: str | Path, kin_root: str | Path) -> ResolvedPhase01APaths:
    stat_root_path = Path(stat_root)
    kin_root_path = Path(kin_root)
    stat_runs = sorted(
        path
        for path in stat_root_path.iterdir()
        if path.is_dir() and path.name.startswith("SLL_REAL_PCMCI_LAG")
    )
    if not stat_runs:
        raise FileNotFoundError(f"No statistical lag runs found under {stat_root_path}")
    stat_identity_run = next(
        (path for path in stat_runs if "LAG01" in path.name),
        stat_runs[0],
    )
    kin_real_only_root = kin_root_path / "SLL_20260426_133037_real_only"
    resolved = ResolvedPhase01APaths(
        stat_root=stat_root_path,
        kin_root=kin_root_path,
        stat_identity_run=stat_identity_run,
        stat_analysis_view_observed=stat_identity_run / "intermediate" / "analysis_view_observed.tsv",
        stat_csv_contract_normalized=stat_identity_run / "intermediate" / "csv_contract_normalized.tsv",
        stat_availability_matrix=stat_identity_run / "audit" / "availability_matrix.tsv",
        stat_label_mapping_audit=stat_identity_run / "audit" / "label_mapping_audit.tsv",
        kin_real_only_root=kin_real_only_root,
        kin_growth_source_audit=kin_real_only_root / "93_growth_windows" / "growth_source_audit.tsv",
        kin_metabolite_handoff=kin_real_only_root / "95_audit" / "metabolite_interval_rates_handoff.tsv",
        kin_report_contract_summary=kin_root_path / "report_contract_summary.json",
    )
    missing = [str(path) for path in resolved.__dict__.values() if isinstance(path, Path) and not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Phase 01A surfaces: " + "; ".join(missing))
    return resolved


def resolve_phase01b_paths(
    repo_root: str | Path,
    stat_root: str | Path,
    kin_root: str | Path,
    out_root: str | Path,
    *,
    strict: bool,
) -> ResolvedPhase01BPaths:
    repo_root_path = Path(repo_root).resolve(strict=False)
    stat_root_path = Path(stat_root).resolve(strict=False)
    kin_root_path = Path(kin_root).resolve(strict=False)
    requested_out_root = Path(out_root).resolve(strict=False)
    allowed_results_root = DEFAULT_RESULTS_ROOT.resolve(strict=False)

    if requested_out_root == repo_root_path or is_same_or_within(requested_out_root, repo_root_path):
        raise Phase01BPathError(
            PHASE01B_REPO_OUTPUT_REJECTION_CODE,
            f"{PHASE01B_REPO_OUTPUT_REJECTION_CODE}: out-root {requested_out_root} is inside repo {repo_root_path}",
        )
    if not is_same_or_within(requested_out_root, allowed_results_root):
        raise Phase01BPathError(
            "PHASE01B_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"out-root {requested_out_root} is outside allowed results root {allowed_results_root}",
        )

    stat_runs_by_lag: dict[int, Path] = {}
    lag_candidates: dict[int, list[Path]] = {}
    for child in sorted(stat_root_path.iterdir()):
        if not child.is_dir():
            continue
        match = LAG_FOLDER_RE.match(child.name)
        if not match:
            continue
        lag = int(match.group("lag"))
        lag_candidates.setdefault(lag, []).append(child)
    if strict:
        missing = [lag for lag in (1, 2, 3, 4) if lag not in lag_candidates]
        duplicates = [lag for lag, candidates in lag_candidates.items() if len(candidates) != 1 and lag in {1, 2, 3, 4}]
        if missing or duplicates:
            raise Phase01BPathError(
                "PHASE01B_STRICT_STAT_LAG_DISCOVERY_FAILED",
                f"Strict LAG discovery failed. missing={missing} duplicates={duplicates}",
            )
    for lag, candidates in lag_candidates.items():
        if len(candidates) == 1:
            stat_runs_by_lag[lag] = candidates[0]
    stat_runs: dict[int, StatRunSurfaceSet] = {}
    for lag, folder in sorted(stat_runs_by_lag.items()):
        surfaces = {relative: _surface_path(folder, relative) for relative in STAT_RUN_REQUIRED_SURFACES}
        stat_runs[lag] = StatRunSurfaceSet(
            run_folder=folder,
            run_max_lag=lag,
            effects=surfaces["results/effects.tsv"],
            network_partialcorr=surfaces["results/network_partialcorr.tsv"],
            interdependence_windows=surfaces["results/interdependence_windows.tsv"],
            snapshots=surfaces["tables/snapshots.tsv"],
            window_deltas=surfaces["tables/window_deltas.tsv"],
            pcmci_dense_replicate_input=surfaces["intermediate/pcmci_dense_replicate_input.tsv"],
            dense_series_interpolated=surfaces["intermediate/dense_series_interpolated.tsv"],
            analysis_view_observed=surfaces["intermediate/analysis_view_observed.tsv"],
            pcmci_qc=surfaces["audit/pcmci_qc.json"],
            partialcorr_qc=surfaces["audit/partialcorr_qc.json"],
            pcmci_dense_qc=surfaces["audit/pcmci_dense_qc.json"],
            postrun_statistical_audits=surfaces["audit/postrun_statistical_audits.tsv"],
            series_index=surfaces["audit/series_index.tsv"],
            availability_matrix=surfaces["audit/availability_matrix.tsv"],
            schema_check=surfaces["qc/schema_check.tsv"],
            run_manifest=surfaces["manifest/run_manifest.json"],
        )

    kin_real_only_root = kin_root_path / "SLL_20260426_133037_real_only"
    kin_real_plus_root = kin_root_path / "SLL_20260426_133037_real_plus_interpolated"
    runtime_root = requested_out_root / f"{PHASE01B_RUNTIME_PREFIX}{utc_stamp()}"

    required_paths = [
        repo_root_path,
        stat_root_path,
        kin_root_path,
        kin_real_only_root,
        kin_real_plus_root,
        kin_root_path / "report_output_catalog.tsv",
        kin_root_path / "report_contract_summary.json",
        kin_root_path / "report_contract_metrics.tsv",
    ]
    for stat_run in stat_runs.values():
        required_paths.extend(
            [
                stat_run.effects,
                stat_run.network_partialcorr,
                stat_run.interdependence_windows,
                stat_run.snapshots,
                stat_run.window_deltas,
                stat_run.pcmci_dense_replicate_input,
                stat_run.dense_series_interpolated,
                stat_run.analysis_view_observed,
                stat_run.pcmci_qc,
                stat_run.partialcorr_qc,
                stat_run.pcmci_dense_qc,
                stat_run.postrun_statistical_audits,
                stat_run.series_index,
                stat_run.availability_matrix,
                stat_run.schema_check,
                stat_run.run_manifest,
            ]
        )
    required_paths.extend(kin_real_only_root / Path(relative.replace("/", "\\")) for relative in KINETIC_REAL_ONLY_REQUIRED_SURFACES)
    required_paths.extend(kin_real_only_root / Path(relative.replace("/", "\\")) for relative in KINETIC_REAL_ONLY_OPTIONAL_SURFACES)
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Phase 01B surfaces: " + "; ".join(missing))

    return ResolvedPhase01BPaths(
        repo_root=repo_root_path,
        stat_root=stat_root_path,
        kin_root=kin_root_path,
        requested_out_root=requested_out_root,
        allowed_results_root=allowed_results_root,
        runtime_root=runtime_root,
        stat_runs=stat_runs,
        kin_real_only_root=kin_real_only_root,
        kin_real_plus_root=kin_real_plus_root,
        kin_report_output_catalog=kin_root_path / "report_output_catalog.tsv",
        kin_report_contract_summary=kin_root_path / "report_contract_summary.json",
        kin_report_contract_metrics=kin_root_path / "report_contract_metrics.tsv",
    )


def resolve_phase01b_join_repair_paths(
    repo_root: str | Path,
    phase01b_runtime: str | Path,
    out_root: str | Path,
) -> ResolvedPhase01BJoinRepairPaths:
    repo_root_path = Path(repo_root).resolve(strict=False)
    phase01b_runtime_path = Path(phase01b_runtime).resolve(strict=False)
    requested_out_root = Path(out_root).resolve(strict=False)
    allowed_results_root = DEFAULT_RESULTS_ROOT.resolve(strict=False)

    if requested_out_root == repo_root_path or is_same_or_within(requested_out_root, repo_root_path):
        raise Phase01BPathError(
            PHASE01B_REPO_OUTPUT_REJECTION_CODE,
            f"{PHASE01B_REPO_OUTPUT_REJECTION_CODE}: out-root {requested_out_root} is inside repo {repo_root_path}",
        )
    if not is_same_or_within(requested_out_root, allowed_results_root):
        raise Phase01BPathError(
            "PHASE01B_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"out-root {requested_out_root} is outside allowed results root {allowed_results_root}",
        )
    if not is_same_or_within(phase01b_runtime_path, allowed_results_root):
        raise Phase01BPathError(
            "PHASE01B_RUNTIME_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"phase01b-runtime {phase01b_runtime_path} is outside allowed results root {allowed_results_root}",
        )

    required_paths = [
        repo_root_path,
        phase01b_runtime_path,
        phase01b_runtime_path / "manifest" / "runtime_manifest.json",
        phase01b_runtime_path / "audit" / "phase01b_validation_summary.tsv",
        phase01b_runtime_path / "data" / "input_join_key_audit.tsv",
    ]
    required_paths.extend(
        phase01b_runtime_path / Path(relative_path.replace("/", "\\"))
        for relative_path in PHASE01B_REQUIRED_OUTPUTS
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Phase 01B runtime artifacts: " + "; ".join(missing))

    runtime_root = requested_out_root / f"{PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX}{utc_stamp()}"
    return ResolvedPhase01BJoinRepairPaths(
        repo_root=repo_root_path,
        phase01b_runtime=phase01b_runtime_path,
        requested_out_root=requested_out_root,
        allowed_results_root=allowed_results_root,
        runtime_root=runtime_root,
        input_manifest=phase01b_runtime_path / "manifest" / "runtime_manifest.json",
        input_validation_summary=phase01b_runtime_path / "audit" / "phase01b_validation_summary.tsv",
        input_join_audit=phase01b_runtime_path / "data" / "input_join_key_audit.tsv",
    )


def resolve_phase02_paths(
    repo_root: str | Path,
    phase01b_runtime: str | Path,
    out_root: str | Path,
    *,
    strict: bool,
) -> ResolvedPhase02Paths:
    del strict
    repo_root_path = Path(repo_root).resolve(strict=False)
    phase01b_runtime_path = Path(phase01b_runtime).resolve(strict=False)
    requested_out_root = Path(out_root).resolve(strict=False)
    allowed_results_root = DEFAULT_RESULTS_ROOT.resolve(strict=False)

    if requested_out_root == repo_root_path or is_same_or_within(requested_out_root, repo_root_path):
        raise Phase02PathError(
            PHASE02_REPO_OUTPUT_REJECTION_CODE,
            f"{PHASE02_REPO_OUTPUT_REJECTION_CODE}: out-root {requested_out_root} is inside repo {repo_root_path}",
        )
    if not is_same_or_within(requested_out_root, allowed_results_root):
        raise Phase02PathError(
            "PHASE02_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"out-root {requested_out_root} is outside allowed results root {allowed_results_root}",
        )
    if not is_same_or_within(phase01b_runtime_path, allowed_results_root):
        raise Phase02PathError(
            "PHASE02_INPUT_RUNTIME_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"phase01b-runtime {phase01b_runtime_path} is outside allowed results root {allowed_results_root}",
        )

    required_paths = [
        repo_root_path,
        phase01b_runtime_path,
    ]
    required_paths.extend(
        phase01b_runtime_path / Path(relative_path.replace("/", "\\"))
        for relative_path in PHASE02_REQUIRED_INPUTS
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Phase 02 input artifacts: " + "; ".join(missing))

    runtime_root = requested_out_root / f"{PHASE02_RUNTIME_PREFIX}{utc_stamp()}"
    return ResolvedPhase02Paths(
        repo_root=repo_root_path,
        phase01b_runtime=phase01b_runtime_path,
        requested_out_root=requested_out_root,
        allowed_results_root=allowed_results_root,
        runtime_root=runtime_root,
        input_manifest=phase01b_runtime_path / "manifest" / "runtime_manifest.json",
        input_validation_summary=phase01b_runtime_path / "audit" / "phase01b_validation_summary.tsv",
    )


def resolve_phase03a_paths(
    repo_root: str | Path,
    phase02_runtime: str | Path,
    out_root: str | Path,
    *,
    strict: bool,
) -> ResolvedPhase03APaths:
    del strict
    repo_root_path = Path(repo_root).resolve(strict=False)
    phase02_runtime_path = Path(phase02_runtime).resolve(strict=False)
    requested_out_root = Path(out_root).resolve(strict=False)
    allowed_results_root = DEFAULT_RESULTS_ROOT.resolve(strict=False)

    if requested_out_root == repo_root_path or is_same_or_within(requested_out_root, repo_root_path):
        raise Phase03APathError(
            PHASE03A_REPO_OUTPUT_REJECTION_CODE,
            f"{PHASE03A_REPO_OUTPUT_REJECTION_CODE}: out-root {requested_out_root} is inside repo {repo_root_path}",
        )
    if not is_same_or_within(requested_out_root, allowed_results_root):
        raise Phase03APathError(
            "PHASE03A_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"out-root {requested_out_root} is outside allowed results root {allowed_results_root}",
        )
    if not is_same_or_within(phase02_runtime_path, allowed_results_root):
        raise Phase03APathError(
            "PHASE03A_INPUT_RUNTIME_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"phase02-runtime {phase02_runtime_path} is outside allowed results root {allowed_results_root}",
        )

    required_paths = [
        repo_root_path,
        phase02_runtime_path,
    ]
    required_paths.extend(
        phase02_runtime_path / Path(relative_path.replace("/", "\\"))
        for relative_path in PHASE03A_REQUIRED_INPUTS
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required Phase 03A input artifacts: " + "; ".join(missing))

    runtime_root = requested_out_root / f"{PHASE03A_RUNTIME_PREFIX}{utc_stamp()}"
    return ResolvedPhase03APaths(
        repo_root=repo_root_path,
        phase02_runtime=phase02_runtime_path,
        requested_out_root=requested_out_root,
        allowed_results_root=allowed_results_root,
        runtime_root=runtime_root,
        input_manifest=phase02_runtime_path / "manifest" / "runtime_manifest.json",
        input_validation_summary=phase02_runtime_path / "audit" / "phase02_validation_summary.tsv",
    )


def resolve_phase03b1_paths(
    repo_root: str | Path,
    phase03a_runtime: str | Path,
    out_root: str | Path,
    *,
    strict: bool,
) -> ResolvedPhase03B1Paths:
    del strict
    repo_root_path = Path(repo_root).resolve(strict=False)
    phase03a_runtime_path = Path(phase03a_runtime).resolve(strict=False)
    requested_out_root = Path(out_root).resolve(strict=False)
    allowed_results_root = DEFAULT_RESULTS_ROOT.resolve(strict=False)

    if not repo_root_path.exists():
        raise FileNotFoundError(f"repo-root does not exist: {repo_root_path}")
    if requested_out_root == repo_root_path or is_same_or_within(requested_out_root, repo_root_path):
        raise Phase03B1PathError(
            PHASE03B1_REPO_OUTPUT_REJECTION_CODE,
            f"{PHASE03B1_REPO_OUTPUT_REJECTION_CODE}: out-root {requested_out_root} is inside repo {repo_root_path}",
        )
    if not is_same_or_within(requested_out_root, allowed_results_root):
        raise Phase03B1PathError(
            "PHASE03B1_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"out-root {requested_out_root} is outside allowed results root {allowed_results_root}",
        )
    if not is_same_or_within(phase03a_runtime_path, allowed_results_root):
        raise Phase03B1PathError(
            "PHASE03B1_INPUT_RUNTIME_OUTSIDE_ALLOWED_RESULTS_ROOT",
            f"phase03a-runtime {phase03a_runtime_path} is outside allowed results root {allowed_results_root}",
        )

    runtime_root = requested_out_root / f"{PHASE03B1_RUNTIME_PREFIX}{utc_stamp()}"
    return ResolvedPhase03B1Paths(
        repo_root=repo_root_path,
        phase03a_runtime=phase03a_runtime_path,
        requested_out_root=requested_out_root,
        allowed_results_root=allowed_results_root,
        runtime_root=runtime_root,
        input_manifest=phase03a_runtime_path / "manifest" / "runtime_manifest.json",
        input_validation_summary=phase03a_runtime_path / "audit" / "phase03_validation_summary.tsv",
    )
