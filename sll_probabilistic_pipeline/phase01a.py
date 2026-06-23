"""Phase 01A identity inventory runtime."""

from __future__ import annotations

from pathlib import Path

from .config import PHASE01A_OUTPUTS
from .io.component_registry import build_canonical_component_alias_registry
from .paths import resolve_phase01a_paths
from .standardize.component_roles import (
    build_acetate_dual_role_audit,
    build_component_role_by_condition_audit,
)
from .standardize.growth_identity import build_growth_variable_identity_audit
from .standardize.join_identity import (
    build_cross_layer_join_identity_policy,
    classify_identity_closure_state,
)
from .utils import ensure_dir, read_tsv, utc_now_iso, write_json, write_tsv


PHASE01A_OUTPUT_FIELDS: dict[str, list[str]] = {
    "growth_variable_identity_audit.tsv": [
        "raw_label",
        "canonical_growth_id",
        "growth_value_type",
        "source_layer",
        "source_surface",
        "source_column",
        "source_row_key",
        "transformation_applied",
        "transformation_formula_if_known",
        "is_directly_observed",
        "is_derived",
        "can_join_to_statistical_lnOD",
        "can_join_to_kinetic_OD600",
        "notes",
    ],
    "acetate_dual_role_audit.tsv": [
        "scenario",
        "scenario_canonical",
        "condition_id",
        "condition_role",
        "raw_label",
        "canonical_component_id",
        "role_as_basal_axis",
        "role_as_added_perturbator",
        "basis_for_added_perturbator",
        "ctrl_reference_available",
        "test_delta_available",
        "source_surface",
        "source_row_key",
        "source_column",
        "notes",
    ],
    "canonical_component_alias_registry.tsv": [
        "raw_label",
        "canonical_component_id",
        "canonical_display_label",
        "component_class",
        "is_basal_axis_member",
        "can_be_target",
        "can_be_perturbator",
        "can_be_added_perturbator_when_test_delta_exists",
        "source_layer",
        "source_surface",
        "source_column",
        "normalization_rule",
        "confidence",
        "manual_review_required",
        "notes",
    ],
    "component_role_by_condition_audit.tsv": [
        "condition_id",
        "scenario",
        "scenario_canonical",
        "condition_role",
        "raw_label",
        "canonical_component_id",
        "component_class",
        "role_as_basal_axis",
        "role_as_added_perturbator",
        "basis_for_added_perturbator",
        "ctrl_reference_available",
        "test_delta_available",
        "source_surface",
        "source_row_key",
        "notes",
    ],
    "cross_layer_join_identity_policy.tsv": [
        "canonical_component_id",
        "condition_id",
        "scenario_canonical",
        "condition_role",
        "source_layer_left",
        "source_surface_left",
        "value_type_left",
        "evidence_scope_left",
        "source_layer_right",
        "source_surface_right",
        "value_type_right",
        "evidence_scope_right",
        "join_decision",
        "decision_basis",
        "raw_measure_identity",
        "notes",
    ],
}


def build_phase01a_policy_artifacts(
    stat_root: str | Path,
    kin_root: str | Path,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, object]]:
    resolved = resolve_phase01a_paths(stat_root, kin_root)

    stat_rows = read_tsv(resolved.stat_analysis_view_observed)
    label_mapping_rows = read_tsv(resolved.stat_label_mapping_audit)
    kin_growth_rows = read_tsv(resolved.kin_growth_source_audit)
    kin_rate_rows = read_tsv(resolved.kin_metabolite_handoff)

    alias_rows = build_canonical_component_alias_registry(
        stat_rows=stat_rows,
        kin_rate_rows=kin_rate_rows,
        kin_growth_rows=kin_growth_rows,
        label_mapping_rows=label_mapping_rows,
    )
    growth_rows = build_growth_variable_identity_audit(
        stat_rows=stat_rows,
        kin_growth_rows=kin_growth_rows,
    )
    acetate_rows = build_acetate_dual_role_audit(stat_rows=stat_rows)
    component_role_rows = build_component_role_by_condition_audit(
        stat_rows=stat_rows,
        alias_rows=alias_rows,
        acetate_rows=acetate_rows,
    )
    join_policy_rows = build_cross_layer_join_identity_policy(
        stat_rows=stat_rows,
        kin_growth_rows=kin_growth_rows,
        kin_rate_rows=kin_rate_rows,
        acetate_rows=acetate_rows,
    )

    outputs = {
        "growth_variable_identity_audit.tsv": growth_rows,
        "acetate_dual_role_audit.tsv": acetate_rows,
        "canonical_component_alias_registry.tsv": alias_rows,
        "component_role_by_condition_audit.tsv": component_role_rows,
        "cross_layer_join_identity_policy.tsv": join_policy_rows,
    }
    summary = {
        "stat_root": str(resolved.stat_root),
        "kin_root": str(resolved.kin_root),
        "stat_identity_run": str(resolved.stat_identity_run),
        "identity_go_state_if_full_release_were_attempted": classify_identity_closure_state(
            growth_rows,
            acetate_rows,
        ),
    }
    return outputs, summary


def write_phase01a_policy_artifacts(
    data_dir: Path,
    artifacts: dict[str, list[dict[str, object]]],
) -> None:
    ensure_dir(data_dir)
    for filename in PHASE01A_OUTPUTS:
        write_tsv(data_dir / filename, artifacts[filename], PHASE01A_OUTPUT_FIELDS[filename])


def run_phase01a(
    stat_root: str | Path,
    kin_root: str | Path,
    out_root: str | Path,
) -> dict[str, object]:
    artifacts, summary = build_phase01a_policy_artifacts(stat_root, kin_root)

    out_root_path = Path(out_root)
    data_dir = ensure_dir(out_root_path / "data")
    manifest_dir = ensure_dir(out_root_path / "manifest")
    ensure_dir(out_root_path / "logs")

    write_phase01a_policy_artifacts(data_dir, artifacts)
    manifest = {
        "phase": "phase01a",
        "generated_at_utc": utc_now_iso(),
        "stat_root": summary["stat_root"],
        "kin_root": summary["kin_root"],
        "stat_identity_run": summary["stat_identity_run"],
        "outputs": list(PHASE01A_OUTPUTS),
        "phase_status": "phase01a_complete_waiting_for_phase01b_approval",
        "identity_go_state_if_full_release_were_attempted": summary[
            "identity_go_state_if_full_release_were_attempted"
        ],
    }
    write_json(manifest_dir / "runtime_manifest.json", manifest)
    return manifest
