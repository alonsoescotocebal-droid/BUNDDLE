"""Cross-layer join identity policy."""

from __future__ import annotations

from collections import defaultdict

from ..paths import canonicalize_scenario, classify_condition_role
from ..utils import unique_by


def build_cross_layer_join_identity_policy(
    stat_rows: list[dict[str, str]],
    kin_growth_rows: list[dict[str, str]],
    kin_rate_rows: list[dict[str, str]],
    acetate_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    stat_growth_pairs = sorted(
        {
            (
                row["condition_id"],
                canonicalize_scenario(row["scenario"]),
                classify_condition_role(
                    row["condition_id"],
                    row.get("paired_condition_id", ""),
                    row.get("family", ""),
                ),
            )
            for row in stat_rows
            if row.get("variable") == "lnOD"
        }
    )
    kin_growth_pairs = {
        (row["condition_id"], canonicalize_scenario(row["scenario"]))
        for row in kin_growth_rows
    }
    for condition_id, scenario_canonical, condition_role in stat_growth_pairs:
        if (condition_id, scenario_canonical) not in kin_growth_pairs:
            continue
        rows.extend(
            [
                {
                    "canonical_component_id": "growth_node",
                    "condition_id": condition_id,
                    "scenario_canonical": scenario_canonical,
                    "condition_role": condition_role,
                    "source_layer_left": "statistical",
                    "source_surface_left": "intermediate/analysis_view_observed.tsv",
                    "value_type_left": "lnOD",
                    "evidence_scope_left": "growth_context",
                    "source_layer_right": "kinetic",
                    "source_surface_right": "93_growth_windows/growth_source_audit.tsv",
                    "value_type_right": "raw_OD600",
                    "evidence_scope_right": "growth_context",
                    "join_decision": "forbidden",
                    "decision_basis": "raw_vs_transformed_growth_mismatch",
                    "raw_measure_identity": "no",
                    "notes": "Statistical lnOD must not be equated to kinetic raw OD600.",
                },
                {
                    "canonical_component_id": "growth_node",
                    "condition_id": condition_id,
                    "scenario_canonical": scenario_canonical,
                    "condition_role": condition_role,
                    "source_layer_left": "statistical",
                    "source_surface_left": "intermediate/analysis_view_observed.tsv",
                    "value_type_left": "lnOD",
                    "evidence_scope_left": "growth_context",
                    "source_layer_right": "kinetic",
                    "source_surface_right": "93_growth_windows/growth_source_audit.tsv",
                    "value_type_right": "normalized_OD600",
                    "evidence_scope_right": "growth_context",
                    "join_decision": "contextual_only",
                    "decision_basis": "statistical_formula_unknown_kinetic_formula_known",
                    "raw_measure_identity": "no",
                    "notes": "Allowed only as contextual growth evidence until formula compatibility is proven.",
                },
                {
                    "canonical_component_id": "growth_node",
                    "condition_id": condition_id,
                    "scenario_canonical": scenario_canonical,
                    "condition_role": condition_role,
                    "source_layer_left": "statistical",
                    "source_surface_left": "intermediate/analysis_view_observed.tsv",
                    "value_type_left": "ln_abs_minus_abs0",
                    "evidence_scope_left": "growth_context",
                    "source_layer_right": "kinetic",
                    "source_surface_right": "93_growth_windows/growth_source_audit.tsv",
                    "value_type_right": "normalized_OD600",
                    "evidence_scope_right": "growth_context",
                    "join_decision": "contextual_only",
                    "decision_basis": "transform_similarity_not_raw_identity",
                    "raw_measure_identity": "no",
                    "notes": "Do not silently equate ln(abs-abs0) to lnOD without contract or formula proof.",
                },
                {
                    "canonical_component_id": "growth_node",
                    "condition_id": condition_id,
                    "scenario_canonical": scenario_canonical,
                    "condition_role": condition_role,
                    "source_layer_left": "statistical",
                    "source_surface_left": "intermediate/analysis_view_observed.tsv",
                    "value_type_left": "raw_OD600",
                    "evidence_scope_left": "growth_context",
                    "source_layer_right": "kinetic",
                    "source_surface_right": "93_growth_windows/growth_source_audit.tsv",
                    "value_type_right": "raw_OD600",
                    "evidence_scope_right": "growth_context",
                    "join_decision": "contextual_only",
                    "decision_basis": "traceability_only_not_primary_statistical_surface",
                    "raw_measure_identity": "yes",
                    "notes": "Raw OD600 label alignment is traceable, but Phase 01A does not promote it to primary statistical identity.",
                },
            ]
        )

    acetate_by_condition = {
        (row["condition_id"], canonicalize_scenario(row["scenario"])): row
        for row in acetate_rows
    }
    stat_components: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in stat_rows:
        canonical = "growth_node" if row.get("variable") == "lnOD" else row.get("variable", "")
        stat_components[(row["condition_id"], canonicalize_scenario(row["scenario"]))].add(canonical)

    shared_rate_rows: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in kin_rate_rows:
        scenario_canonical = canonicalize_scenario(row["scenario"])
        raw = row.get("variable", "")
        canonical = {
            "Acetic acid": "acetate_gL",
            "Fumarate": "fumarate_gL",
            "Lactic acid": "lactic_gL",
            "Succinic acid": "succinate_gL",
            "Tartaric acid": "tartaric_gL",
            "Tyrosol": "tyrosol_gL",
            "ln(abs-abs0)": "growth_node",
        }.get(raw)
        if canonical:
            shared_rate_rows[(row["condition_id"], scenario_canonical)].add(canonical)

    for key, components in sorted(shared_rate_rows.items()):
        condition_id, scenario_canonical = key
        condition_role = "control" if condition_id.endswith("_Control") else "test"
        stat_component_set = stat_components.get(key, set())
        for canonical_component_id in sorted(components & stat_component_set):
            if canonical_component_id == "growth_node":
                continue
            scopes = ["target_state"]
            acetate = acetate_by_condition.get(key)
            if canonical_component_id == "acetate_gL" and acetate:
                scopes = ["basal_axis_component"]
                if acetate.get("role_as_added_perturbator") == "yes":
                    scopes.append("added_perturbator_component")
                elif acetate.get("role_as_added_perturbator") == "undetermined":
                    scopes.append("added_perturbator_component")
            for scope in scopes:
                rows.append(
                    {
                        "canonical_component_id": canonical_component_id,
                        "condition_id": condition_id,
                        "scenario_canonical": scenario_canonical,
                        "condition_role": condition_role,
                        "source_layer_left": "statistical",
                        "source_surface_left": "intermediate/analysis_view_observed.tsv",
                        "value_type_left": "concentration_g_per_L",
                        "evidence_scope_left": scope,
                        "source_layer_right": "kinetic",
                        "source_surface_right": "95_audit/metabolite_interval_rates_handoff.tsv",
                        "value_type_right": "volumetric_rate_per_h",
                        "evidence_scope_right": "target_state",
                        "join_decision": "contextual_only",
                        "decision_basis": "same_component_different_measurement_surface",
                        "raw_measure_identity": "no",
                        "notes": "Same canonical component across layers, but concentration and rate are not raw-measure identity.",
                    }
                )
    return unique_by(
        rows,
        (
            "canonical_component_id",
            "condition_id",
            "scenario_canonical",
            "source_layer_left",
            "value_type_left",
            "evidence_scope_left",
            "source_layer_right",
            "value_type_right",
            "evidence_scope_right",
        ),
    )


def classify_identity_closure_state(
    growth_rows: list[dict[str, str]],
    acetate_rows: list[dict[str, str]],
) -> str:
    for row in growth_rows:
        if not row.get("source_surface") or not row.get("source_row_key") or not row.get("source_column"):
            return "internal_failure_localized"
    for row in acetate_rows:
        if not row.get("source_surface") or not row.get("source_row_key"):
            return "internal_failure_localized"
        if row.get("role_as_added_perturbator") == "undetermined":
            return "external_validation_required"
    if any(
        row.get("growth_value_type") in {"lnOD", "ln_abs_minus_abs0", "normalized_OD600"}
        and row.get("transformation_formula_if_known") == "unknown_from_source"
        for row in growth_rows
    ):
        return "external_validation_required"
    return "phase01a_inventory_complete"
