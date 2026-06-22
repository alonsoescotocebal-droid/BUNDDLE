"""Path resolution for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import SCENARIO_ALIASES


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


def canonicalize_scenario(value: str) -> str:
    return SCENARIO_ALIASES.get(value, value)


def classify_condition_role(condition_id: str, paired_condition_id: str, family: str = "") -> str:
    if family == "Control":
        return "control"
    if condition_id.endswith("_Control"):
        return "control"
    if not paired_condition_id:
        return "control"
    return "test"


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

