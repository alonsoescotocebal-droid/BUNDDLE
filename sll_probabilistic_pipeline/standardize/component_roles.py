"""Component-role inventory logic."""

from __future__ import annotations

from collections import defaultdict

from ..paths import canonicalize_scenario, classify_condition_role
from ..utils import as_float, unique_by


def build_acetate_dual_role_audit(stat_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    acetate_rows = [
        row
        for row in stat_rows
        if row.get("variable") == "acetate_gL"
    ]
    observed_t0 = [
        row
        for row in acetate_rows
        if row.get("flag") == "OBSERVED_EXCEL" and as_float(row.get("time_h")) == 0.0
    ]
    rows_by_condition: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in observed_t0:
        rows_by_condition[(row["condition_id"], row["scenario"])].append(row)

    results: list[dict[str, object]] = []
    for (condition_id, scenario), rows in sorted(rows_by_condition.items()):
        sample = rows[0]
        paired_condition_id = sample.get("paired_condition_id", "")
        condition_role = classify_condition_role(
            condition_id,
            paired_condition_id,
            sample.get("family", ""),
        )
        control_rows = rows_by_condition.get((paired_condition_id, scenario), [])
        ctrl_reference_available = bool(control_rows)
        test_delta_available = bool(rows) and bool(control_rows)
        delta = None
        if test_delta_available:
            test_mean = sum(as_float(row["value"]) or 0.0 for row in rows) / len(rows)
            ctrl_mean = sum(as_float(row["value"]) or 0.0 for row in control_rows) / len(control_rows)
            delta = test_mean - ctrl_mean
        explicit_test_addition = False
        if condition_role == "control":
            added_role = "no"
            basis = "not_applicable"
        elif explicit_test_addition:
            added_role = "yes"
            basis = "explicit_test_addition"
        elif test_delta_available and delta is not None:
            added_role = "yes" if abs(delta) > 1e-9 else "no"
            basis = "concentration_differs_from_ctrl"
        else:
            added_role = "undetermined"
            basis = "insufficient_source"

        control_keys = ",".join(row.get("row_identity_id", "") for row in control_rows)
        test_keys = ",".join(row.get("row_identity_id", "") for row in rows)
        results.append(
            {
                "scenario": scenario,
                "scenario_canonical": canonicalize_scenario(scenario),
                "condition_id": condition_id,
                "condition_role": condition_role,
                "raw_label": sample.get("assay_id", "Acetic acid"),
                "canonical_component_id": "acetate_gL",
                "role_as_basal_axis": "yes",
                "role_as_added_perturbator": added_role,
                "basis_for_added_perturbator": basis,
                "ctrl_reference_available": "yes" if ctrl_reference_available else "no",
                "test_delta_available": "yes" if test_delta_available else "no",
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_row_key": sample.get("row_identity_id", ""),
                "source_column": "assay_id",
                "notes": (
                    f"paired_condition_id={paired_condition_id or 'none'}; "
                    f"test_t0_row_keys={test_keys or 'none'}; "
                    f"ctrl_t0_row_keys={control_keys or 'none'}; "
                    f"delta_t0={delta if delta is not None else 'not_available'}; "
                    "explicit_test_addition_source=not_found_phase01a"
                ),
            }
        )
    return results


def build_component_role_by_condition_audit(
    stat_rows: list[dict[str, str]],
    alias_rows: list[dict[str, str]],
    acetate_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    alias_by_canonical: dict[str, dict[str, str]] = {}
    for row in alias_rows:
        alias_by_canonical.setdefault(row["canonical_component_id"], row)

    acetate_by_condition = {
        (row["condition_id"], row["scenario"]): row
        for row in acetate_rows
    }
    seen_components: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in stat_rows:
        scenario = row.get("scenario", "")
        condition_id = row.get("condition_id", "")
        if row.get("variable") == "lnOD":
            canonical_component_id = "growth_node"
            raw_label = row.get("variable", "")
        else:
            canonical_component_id = row.get("variable", "")
            raw_label = row.get("assay_id", row.get("variable", ""))
        key = (condition_id, scenario)
        seen_components[key].setdefault(canonical_component_id, row | {"_raw_label": raw_label})

    results: list[dict[str, object]] = []
    for (condition_id, scenario), components in sorted(seen_components.items()):
        for canonical_component_id, source_row in sorted(components.items()):
            alias = alias_by_canonical.get(canonical_component_id)
            condition_role = classify_condition_role(
                condition_id,
                source_row.get("paired_condition_id", ""),
                source_row.get("family", ""),
            )
            if canonical_component_id == "acetate_gL":
                acetate = acetate_by_condition[(condition_id, scenario)]
                basal = acetate["role_as_basal_axis"]
                added = acetate["role_as_added_perturbator"]
                basis = acetate["basis_for_added_perturbator"]
                ctrl_reference_available = acetate["ctrl_reference_available"]
                test_delta_available = acetate["test_delta_available"]
                notes = acetate["notes"]
            elif canonical_component_id == "growth_node":
                basal = "no"
                added = "no"
                basis = "not_applicable"
                ctrl_reference_available = "no"
                test_delta_available = "no"
                notes = "Growth family preserved as target/context only in Phase 01A."
            else:
                basal = "no"
                added = "no"
                basis = "not_applicable"
                ctrl_reference_available = "no"
                test_delta_available = "no"
                notes = "Phase 01A keeps non-acetate component role inventory conservative."
            results.append(
                {
                    "condition_id": condition_id,
                    "scenario": scenario,
                    "scenario_canonical": canonicalize_scenario(scenario),
                    "condition_role": condition_role,
                    "raw_label": source_row.get("_raw_label", ""),
                    "canonical_component_id": canonical_component_id,
                    "component_class": alias.get("component_class", "unknown") if alias else "unknown",
                    "role_as_basal_axis": basal,
                    "role_as_added_perturbator": added,
                    "basis_for_added_perturbator": basis,
                    "ctrl_reference_available": ctrl_reference_available,
                    "test_delta_available": test_delta_available,
                    "source_surface": "intermediate/analysis_view_observed.tsv",
                    "source_row_key": source_row.get("row_identity_id", ""),
                    "notes": notes,
                }
            )
    return unique_by(
        results,
        ("condition_id", "scenario", "canonical_component_id"),
    )

