"""Kinetic normalization for Phase 01B."""

from __future__ import annotations

from ..io.readers import LoadedSurface
from ..paths import canonicalize_scenario, classify_condition_role
from ..utils import normalize_label, stable_trace_id


def _alias_lookup(alias_rows: list[dict[str, str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in alias_rows:
        lookup.setdefault(normalize_label(row["raw_label"]), row["canonical_component_id"])
    return lookup


def _canonical_component(raw_label: str, alias_lookup: dict[str, str]) -> str:
    return alias_lookup.get(normalize_label(raw_label), raw_label)


def _trace(
    surface: LoadedSurface,
    row_key: str,
    row_number: int,
) -> dict[str, object]:
    return {
        "source_path": str(surface.path),
        "source_surface": surface.source_surface,
        "source_row_key": row_key,
        "source_row_number": row_number,
        "direct_read_yes_no": "yes",
        "inference_used_yes_no": "no",
        "trace_id": stable_trace_id(surface.source_surface, row_key, row_number),
    }


def build_kinetic_outputs(
    loaded: dict[str, LoadedSurface],
    alias_rows: list[dict[str, str]],
) -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    alias_lookup = _alias_lookup(alias_rows)
    growth_rows: list[dict[str, object]] = []
    rate_rows: list[dict[str, object]] = []
    temporal_rows: list[dict[str, object]] = []
    yield_rows: list[dict[str, object]] = []
    disabled_rows: list[dict[str, object]] = []
    traceability_rows: list[dict[str, object]] = []
    empty_audit_rows: list[dict[str, object]] = []

    growth_source_lookup = {row["group_key"]: row for row in loaded["growth_source_audit"].rows}

    growth_handoff = loaded["growth_windows_handoff"]
    for row_number, row in enumerate(growth_handoff.rows, start=1):
        group_key = row["group_key"]
        source_meta = growth_source_lookup.get(group_key, {})
        condition_id = row["condition_id"]
        scenario = row["scenario"]
        growth_rows.append(
            {
                "source_layer": "kinetic",
                "branch": "real_only",
                "condition_id": condition_id,
                "scenario": scenario,
                "scenario_canonical": canonicalize_scenario(scenario),
                "condition_role": classify_condition_role(condition_id, "", ""),
                "canonical_component_id": "growth_node",
                "variable_raw": source_meta.get("source_variable_used", "OD600"),
                "value_type": "normalized_OD600",
                "evidence_scope": "growth_context",
                **row,
                "growth_source_mode": source_meta.get("growth_source_mode", ""),
                "growth_truth_primary_signal": source_meta.get("growth_truth_primary_signal", ""),
                "source_transform_used": source_meta.get("source_transform_used", ""),
                **_trace(growth_handoff, group_key, row_number),
            }
        )

    metabolite_handoff = loaded["metabolite_interval_rates_handoff"]
    for row_number, row in enumerate(metabolite_handoff.rows, start=1):
        raw_label = row["variable"]
        condition_id = row["condition_id"]
        scenario = row["scenario"]
        row_key = row["group_key"]
        rate_rows.append(
            {
                "source_layer": "kinetic",
                "branch": "real_only",
                "condition_id": condition_id,
                "scenario": scenario,
                "scenario_canonical": canonicalize_scenario(scenario),
                "condition_role": classify_condition_role(condition_id, "", ""),
                "canonical_component_id": _canonical_component(raw_label, alias_lookup),
                "variable_raw": raw_label,
                "value_type": "volumetric_rate_per_h",
                "evidence_scope": "target_state",
                **row,
                **_trace(metabolite_handoff, row_key, row_number),
            }
        )

    temporal_handoff = loaded["temporal_coupling_classification_handoff"]
    for row_number, row in enumerate(temporal_handoff.rows, start=1):
        raw_label = row["variable"]
        condition_id = row["condition_id"]
        scenario = row["scenario"]
        row_key = row["group_key"]
        temporal_rows.append(
            {
                "source_layer": "kinetic",
                "branch": "real_only",
                "condition_id": condition_id,
                "scenario": scenario,
                "scenario_canonical": canonicalize_scenario(scenario),
                "condition_role": classify_condition_role(condition_id, "", ""),
                "canonical_component_id": _canonical_component(raw_label, alias_lookup),
                "variable_raw": raw_label,
                "value_type": "temporal_coupling_classification",
                "evidence_scope": "target_state",
                **row,
                **_trace(temporal_handoff, row_key, row_number),
            }
        )

    yield_handoff = loaded["yield_pairs_handoff"]
    if not yield_handoff.rows:
        empty_audit_rows.append(
            {
                "source_layer": "kinetic",
                "branch_or_run": "real_only",
                "source_surface": yield_handoff.source_surface,
                "source_path": str(yield_handoff.path),
                "empty_status": "empty_legitimate",
                "row_count": 0,
                "basis": "header_only_yield_handoff_with_yield_audit_present",
                "notes": "Yield handoff is header-only; Phase 01B preserves empty output with schema.",
            }
        )
    else:
        for row_number, row in enumerate(yield_handoff.rows, start=1):
            row_key = row["group_key"]
            condition_id = row.get("condition_id", "")
            scenario = row.get("scenario", "")
            yield_rows.append(
                {
                    "source_layer": "kinetic",
                    "branch": "real_only",
                    "condition_id": condition_id,
                    "scenario": scenario,
                    "scenario_canonical": canonicalize_scenario(scenario),
                    "condition_role": classify_condition_role(condition_id, "", ""),
                    "substrate_canonical_component_id": _canonical_component(
                        row.get("substrate_variable", ""),
                        alias_lookup,
                    ),
                    "product_canonical_component_id": _canonical_component(
                        row.get("product_variable", ""),
                        alias_lookup,
                    ),
                    "value_type": "yield_product_per_substrate",
                    "evidence_scope": "target_state",
                    **row,
                    **_trace(yield_handoff, row_key, row_number),
                }
            )

    report_output_catalog = loaded["report_output_catalog"]
    for row_number, row in enumerate(report_output_catalog.rows, start=1):
        if row["branch"] == "real_plus_interpolated":
            disabled_rows.append(
                {
                    "source_layer": "kinetic",
                    "branch": row["branch"],
                    "source_surface": "report_output_catalog.tsv",
                    "relative_path": row["relative_path"],
                    "category": row["category"],
                    "semantic_scope": row["semantic_scope"],
                    "report_surface_role": row["report_surface_role"],
                    "exists": row["exists"],
                    "status": "excluded_by_canonical_rule",
                    "notes": "Inventory only; never used for primary kinetic outputs.",
                    **_trace(report_output_catalog, row["relative_path"], row_number),
                }
            )

    for surface_name in (
        "growth_source_audit",
        "growth_window_audit",
        "growth_windows_best",
        "metabolite_rate_audit",
        "metabolite_interval_rates",
        "partial_mass_balance",
        "methodological_exclusions",
        "kinetic_replicate_consensus_audit",
        "yield_audit",
        "report_output_catalog",
        "report_contract_metrics",
    ):
        surface = loaded[surface_name]
        for row_number, row in enumerate(surface.rows, start=1):
            row_key = row.get("group_key") or row.get("relative_path") or f"{surface_name}|{row_number}"
            traceability_rows.append(
                {
                    "source_layer": "kinetic",
                    "branch": "real_only" if surface_name != "report_output_catalog" else row.get("branch", ""),
                    "traceability_surface_kind": surface_name,
                    "source_surface": surface.source_surface,
                    "source_path": str(surface.path),
                    "row_payload": row,
                    **_trace(surface, row_key, row_number),
                }
            )
    report_summary = loaded["report_contract_summary"]
    assert report_summary.json_payload is not None
    for index, key in enumerate(sorted(report_summary.json_payload.keys()), start=1):
        traceability_rows.append(
            {
                "source_layer": "kinetic",
                "branch": "catalog",
                "traceability_surface_kind": "report_contract_summary",
                "source_surface": report_summary.source_surface,
                "source_path": str(report_summary.path),
                "row_payload": {key: report_summary.json_payload[key]},
                **_trace(report_summary, key, index),
            }
        )

    outputs = {
        "kinetic_growth_primary_long.tsv": growth_rows,
        "kinetic_rate_primary_long.tsv": rate_rows,
        "kinetic_temporal_coupling_primary_long.tsv": temporal_rows,
        "kinetic_yield_primary_long.tsv": yield_rows,
        "kinetic_disabled_branch_inventory.tsv": disabled_rows,
        "kinetic_traceability_long.tsv": traceability_rows,
    }
    return outputs, empty_audit_rows
