"""Join-key auditing for Phase 01B."""

from __future__ import annotations

from collections import Counter


FIXED_JOIN_AXES = (
    "canonical_component_id",
    "scenario_canonical",
    "condition_role",
    "source_layer",
    "value_type",
    "evidence_scope",
)


def build_input_join_key_audit(
    *,
    phase01a_policy_rows: dict[str, list[dict[str, str]]],
    stat_outputs: dict[str, list[dict[str, object]]],
    kinetic_outputs: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.append(
        {
            "left_surface": "cross_layer_join_identity_policy.tsv",
            "right_surface": "phase01a_policy",
            "candidate_keys": ";".join(FIXED_JOIN_AXES),
            "normalized_keys": ";".join(FIXED_JOIN_AXES),
            "comparison_keys": "policy_defined",
            "null_rate_by_key": "not_applicable",
            "unique_key_rate": "not_applicable",
            "many_to_many_risk": "policy_defined",
            "match_rate": "not_applicable",
            "unmatched_left_count": 0,
            "unmatched_right_count": 0,
            "policy_artifact_row_count": len(phase01a_policy_rows["cross_layer_join_identity_policy.tsv"]),
            "notes": "Phase 01B join audit is constrained by immutable Phase 01A policy rows.",
        }
    )
    rows.extend(
        _pair_audit(
            left_surface="stat_descriptive_node_state_long.tsv",
            right_surface="kinetic_rate_primary_long.tsv",
            left_rows=stat_outputs["stat_descriptive_node_state_long.tsv"],
            right_rows=kinetic_outputs["kinetic_rate_primary_long.tsv"],
            comparison_keys=("canonical_component_id", "scenario_canonical", "condition_role"),
        )
    )
    rows.extend(
        _pair_audit(
            left_surface="stat_descriptive_node_state_long.tsv",
            right_surface="kinetic_temporal_coupling_primary_long.tsv",
            left_rows=stat_outputs["stat_descriptive_node_state_long.tsv"],
            right_rows=kinetic_outputs["kinetic_temporal_coupling_primary_long.tsv"],
            comparison_keys=("canonical_component_id", "scenario_canonical", "condition_role"),
        )
    )
    rows.extend(
        _pair_audit(
            left_surface="growth_variable_identity_audit.tsv",
            right_surface="kinetic_growth_primary_long.tsv",
            left_rows=phase01a_policy_rows["growth_variable_identity_audit.tsv"],
            right_rows=kinetic_outputs["kinetic_growth_primary_long.tsv"],
            comparison_keys=("canonical_component_id",),
            left_alias_map={"canonical_component_id": "canonical_growth_id"},
        )
    )
    return rows


def _pair_audit(
    *,
    left_surface: str,
    right_surface: str,
    left_rows: list[dict[str, object]],
    right_rows: list[dict[str, object]],
    comparison_keys: tuple[str, ...],
    left_alias_map: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    left_alias_map = left_alias_map or {}
    left_key_fields = tuple(left_alias_map.get(key, key) for key in comparison_keys)
    right_key_fields = comparison_keys
    left_key_counter = Counter(_key(row, left_key_fields) for row in left_rows)
    right_key_counter = Counter(_key(row, right_key_fields) for row in right_rows)
    left_keys = {key for key in left_key_counter if any(part != "" for part in key)}
    right_keys = {key for key in right_key_counter if any(part != "" for part in key)}
    matched = left_keys & right_keys
    unmatched_left = left_keys - right_keys
    unmatched_right = right_keys - left_keys
    comparison_key_text = ";".join(comparison_keys)
    row = {
        "left_surface": left_surface,
        "right_surface": right_surface,
        "candidate_keys": ";".join(FIXED_JOIN_AXES),
        "normalized_keys": ";".join(FIXED_JOIN_AXES),
        "comparison_keys": comparison_key_text,
        "null_rate_by_key": ";".join(
            f"{key}:{_null_rate(left_rows, left_alias_map.get(key, key)):.6f}|{_null_rate(right_rows, key):.6f}"
            for key in comparison_keys
        ),
        "unique_key_rate": f"{_unique_key_rate(left_rows, left_key_fields):.6f}|{_unique_key_rate(right_rows, right_key_fields):.6f}",
        "many_to_many_risk": "yes"
        if any(count > 1 for count in left_key_counter.values()) and any(count > 1 for count in right_key_counter.values())
        else "no",
        "match_rate": f"{(len(matched) / len(left_keys)) if left_keys else 0.0:.6f}",
        "unmatched_left_count": len(unmatched_left),
        "unmatched_right_count": len(unmatched_right),
        "notes": "Join audit computed on comparison keys while fixed axes remain mandatory policy fields.",
    }
    return [row]


def _key(row: dict[str, object], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in fields)


def _null_rate(rows: list[dict[str, object]], field: str) -> float:
    if not rows:
        return 0.0
    nulls = sum(1 for row in rows if str(row.get(field, "")) == "")
    return nulls / len(rows)


def _unique_key_rate(rows: list[dict[str, object]], key_fields: tuple[str, ...]) -> float:
    if not rows:
        return 0.0
    keys = [_key(row, key_fields) for row in rows]
    return len(set(keys)) / len(rows)
