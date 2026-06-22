"""Canonical component alias registry logic."""

from __future__ import annotations

from collections.abc import Iterable

from ..config import MANUAL_POLICY_SURFACE
from ..utils import normalize_label, unique_by


CANONICAL_COMPONENTS: dict[str, dict[str, str]] = {
    "acetate_gL": {
        "display": "acetate / acetic acid",
        "class": "metabolite",
        "basal_axis": "yes",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "yes",
    },
    "fumarate_gL": {
        "display": "fumarate",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "succinate_gL": {
        "display": "succinate / succinic acid",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "lactic_gL": {
        "display": "lactate / lactic acid",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "tartaric_gL": {
        "display": "tartaric acid",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "tyrosol_gL": {
        "display": "tyrosol",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "catechol_gL": {
        "display": "catechol",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "ethanol_gL": {
        "display": "ethanol",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "glycerol_gL": {
        "display": "glycerol",
        "class": "metabolite",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "yes",
        "added_delta": "no",
    },
    "growth_node": {
        "display": "growth / OD600 family",
        "class": "growth_family",
        "basal_axis": "no",
        "target": "yes",
        "perturbator": "no",
        "added_delta": "no",
    },
}

MANUAL_ALIAS_ROWS = (
    ("Acetic acid", "acetate_gL"),
    ("acetic acid", "acetate_gL"),
    ("acetic_acid", "acetate_gL"),
    ("acetate_gL", "acetate_gL"),
    ("Fumarate", "fumarate_gL"),
    ("fumarate_gL", "fumarate_gL"),
    ("Succinic acid", "succinate_gL"),
    ("succinate_gL", "succinate_gL"),
    ("Lactic acid", "lactic_gL"),
    ("lactic_gL", "lactic_gL"),
    ("Tartaric acid", "tartaric_gL"),
    ("tartaric_gL", "tartaric_gL"),
    ("Tyrosol", "tyrosol_gL"),
    ("tyrosol_gL", "tyrosol_gL"),
    ("OD600", "growth_node"),
    ("lnOD", "growth_node"),
    ("ln(abs-abs0)", "growth_node"),
)


def canonical_component_id(raw_label: str, label_mapping_rows: list[dict[str, str]]) -> str | None:
    manual = {
        normalize_label(raw): canonical
        for raw, canonical in MANUAL_ALIAS_ROWS
    }
    normalized = normalize_label(raw_label)
    if normalized in manual:
        return manual[normalized]
    for row in label_mapping_rows:
        if row.get("column") != "variable":
            continue
        if row.get("mapped") != "yes":
            continue
        if normalize_label(row.get("source_label", "")) == normalized:
            return row.get("canonical_label")
    return None


def build_canonical_component_alias_registry(
    stat_rows: list[dict[str, str]],
    kin_rate_rows: list[dict[str, str]],
    kin_growth_rows: list[dict[str, str]],
    label_mapping_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw_label, canonical in MANUAL_ALIAS_ROWS:
        component = CANONICAL_COMPONENTS[canonical]
        rows.append(
            {
                "raw_label": raw_label,
                "canonical_component_id": canonical,
                "canonical_display_label": component["display"],
                "component_class": component["class"],
                "is_basal_axis_member": component["basal_axis"],
                "can_be_target": component["target"],
                "can_be_perturbator": component["perturbator"],
                "can_be_added_perturbator_when_test_delta_exists": component["added_delta"],
                "source_layer": "manual_policy",
                "source_surface": MANUAL_POLICY_SURFACE,
                "source_column": "raw_label",
                "normalization_rule": "policy_required_alias_registry",
                "confidence": "policy_required",
                "manual_review_required": "no",
                "notes": "Required by Phase 01A identity policy even when absent in runtime surfaces.",
            }
        )

    observed_specs = [
        ("statistical", "intermediate/analysis_view_observed.tsv", "assay_id", {row["assay_id"] for row in stat_rows}),
        ("statistical", "intermediate/analysis_view_observed.tsv", "variable", {row["variable"] for row in stat_rows}),
        ("kinetic", "95_audit/metabolite_interval_rates_handoff.tsv", "variable", {row["variable"] for row in kin_rate_rows}),
        ("kinetic", "93_growth_windows/growth_source_audit.tsv", "source_variable_used", {row["source_variable_used"] for row in kin_growth_rows}),
    ]
    for source_layer, source_surface, source_column, labels in observed_specs:
        for raw_label in sorted(label for label in labels if label):
            canonical = canonical_component_id(raw_label, label_mapping_rows)
            if canonical is None:
                continue
            component = CANONICAL_COMPONENTS[canonical]
            normalization_rule = (
                "growth_family_identity_preserve_value_type"
                if canonical == "growth_node"
                else "canonical_component_alias_map"
            )
            rows.append(
                {
                    "raw_label": raw_label,
                    "canonical_component_id": canonical,
                    "canonical_display_label": component["display"],
                    "component_class": component["class"],
                    "is_basal_axis_member": component["basal_axis"],
                    "can_be_target": component["target"],
                    "can_be_perturbator": component["perturbator"],
                    "can_be_added_perturbator_when_test_delta_exists": component["added_delta"],
                    "source_layer": source_layer,
                    "source_surface": source_surface,
                    "source_column": source_column,
                    "normalization_rule": normalization_rule,
                    "confidence": "source_observed",
                    "manual_review_required": "no",
                    "notes": "Observed alias in runtime surface.",
                }
            )
    return unique_by(
        rows,
        ("raw_label", "canonical_component_id", "source_layer", "source_surface", "source_column"),
    )


def component_metadata(canonical_id: str) -> dict[str, str]:
    return CANONICAL_COMPONENTS[canonical_id]


def canonical_component_ids_from_registry(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        canonical_id = row["canonical_component_id"]
        lookup.setdefault(canonical_id, component_metadata(canonical_id))
    return lookup

