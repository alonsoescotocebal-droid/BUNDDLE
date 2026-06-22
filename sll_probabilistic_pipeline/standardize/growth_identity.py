"""Growth identity inventory logic."""

from __future__ import annotations

from ..utils import unique_by

GROWTH_ASSAY_LABELS = {"OD600", "ln(abs-abs0)"}


def build_growth_variable_identity_audit(
    stat_rows: list[dict[str, str]],
    kin_growth_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in stat_rows:
        if row.get("variable") != "lnOD":
            continue
        row_key = row.get("row_identity_id", "")
        rows.append(
            {
                "raw_label": row["variable"],
                "canonical_growth_id": "growth_node",
                "growth_value_type": "lnOD",
                "source_layer": "statistical",
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_column": "variable",
                "source_row_key": row_key,
                "transformation_applied": "yes",
                "transformation_formula_if_known": "unknown_from_source",
                "is_directly_observed": "no",
                "is_derived": "yes",
                "can_join_to_statistical_lnOD": "yes",
                "can_join_to_kinetic_OD600": "no",
                "notes": f"Canonical statistical growth variable derived from assay_id={row.get('assay_id', '')}.",
            }
        )
        assay_id = row.get("assay_id", "")
        if assay_id not in GROWTH_ASSAY_LABELS:
            continue
        if assay_id == "OD600":
            value_type = "raw_OD600"
            transformation_applied = "no"
            formula = "not_applicable"
            join_stat = "no"
            join_kin = "yes"
            notes = "Direct OD600 source label preserved separately from canonical lnOD variable."
        else:
            value_type = "ln_abs_minus_abs0"
            transformation_applied = "yes"
            formula = "unknown_from_source"
            join_stat = "contextual_only"
            join_kin = "contextual_only"
            notes = "Transformed growth label preserved without assuming raw-measure identity to lnOD."
        rows.append(
            {
                "raw_label": assay_id,
                "canonical_growth_id": "growth_node",
                "growth_value_type": value_type,
                "source_layer": "statistical",
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_column": "assay_id",
                "source_row_key": row_key,
                "transformation_applied": transformation_applied,
                "transformation_formula_if_known": formula,
                "is_directly_observed": "yes",
                "is_derived": "no",
                "can_join_to_statistical_lnOD": join_stat,
                "can_join_to_kinetic_OD600": join_kin,
                "notes": notes,
            }
        )

    for row in kin_growth_rows:
        row_key = row.get("group_key", "")
        rows.append(
            {
                "raw_label": row.get("source_variable_used", ""),
                "canonical_growth_id": "growth_node",
                "growth_value_type": "raw_OD600",
                "source_layer": "kinetic",
                "source_surface": "93_growth_windows/growth_source_audit.tsv",
                "source_column": "source_variable_used",
                "source_row_key": row_key,
                "transformation_applied": "no",
                "transformation_formula_if_known": "not_applicable",
                "is_directly_observed": "yes",
                "is_derived": "no",
                "can_join_to_statistical_lnOD": "no",
                "can_join_to_kinetic_OD600": "yes",
                "notes": "Kinetic layer starts from raw OD600.",
            }
        )
        rows.append(
            {
                "raw_label": row.get("biomass_semantics", ""),
                "canonical_growth_id": "growth_node",
                "growth_value_type": "normalized_OD600",
                "source_layer": "kinetic",
                "source_surface": "93_growth_windows/growth_source_audit.tsv",
                "source_column": "biomass_semantics",
                "source_row_key": row_key,
                "transformation_applied": "yes",
                "transformation_formula_if_known": row.get("biomass_semantics", "") or "unknown_from_source",
                "is_directly_observed": "no",
                "is_derived": "yes",
                "can_join_to_statistical_lnOD": "contextual_only",
                "can_join_to_kinetic_OD600": "contextual_only",
                "notes": f"Kinetic transform token={row.get('source_transform_used', '')}.",
            }
        )
        rows.append(
            {
                "raw_label": row.get("log_signal_role", ""),
                "canonical_growth_id": "growth_node",
                "growth_value_type": "growth_context",
                "source_layer": "kinetic",
                "source_surface": "93_growth_windows/growth_source_audit.tsv",
                "source_column": "log_signal_role",
                "source_row_key": row_key,
                "transformation_applied": "yes",
                "transformation_formula_if_known": row.get("biomass_semantics", "") or "unknown_from_source",
                "is_directly_observed": "no",
                "is_derived": "yes",
                "can_join_to_statistical_lnOD": "contextual_only",
                "can_join_to_kinetic_OD600": "no",
                "notes": "Audited kinetic growth interpretation context.",
            }
        )

    return unique_by(
        rows,
        ("raw_label", "source_layer", "source_surface", "source_column", "source_row_key"),
    )

