"""Join profiling and admissibility contracts for Phase 01B surfaces."""

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

JOIN_RESOLUTION_VALUES = {
    "joinable",
    "projection_only",
    "policy_lookup_only",
    "forbidden",
    "policy_defined",
}

PAIR_SPECS = (
    {
        "left_surface": "stat_descriptive_node_state_long.tsv",
        "right_surface": "kinetic_rate_primary_long.tsv",
        "comparison_keys": ("canonical_component_id", "scenario_canonical", "condition_role"),
        "left_natural_keys": (
            "condition_id",
            "scenario_canonical",
            "condition_role",
            "replicate",
            "canonical_component_id",
            "descriptive_measure_type",
            "timepoint_label",
            "window_label",
        ),
        "right_natural_keys": (
            "condition_id",
            "scenario_canonical",
            "condition_role",
            "replicate",
            "canonical_component_id",
        ),
        "missing_key_dimensions": (
            "condition_id",
            "replicate",
            "descriptive_measure_type",
            "timepoint_label",
            "window_label",
        ),
        "duplicate_origin": "run_max_lag_repetition_across_LAG01_LAG04;multiple_descriptive_measure_rows_per_component",
        "root_cause_kind": "broad_key_omits_condition_replicate_measure_dimensions",
        "join_admissibility": "projection_only",
        "phase02_consumption_mode": "deduplicate_lag_invariant_descriptive_then_project_to_kinetic_component_context",
        "surface_usage_class": "measurement_surface",
        "resolution_notes": (
            "Direct join is forbidden on the broad key. Phase 02 must deduplicate lag-invariant descriptive rows "
            "on the natural key and only project by condition, replicate, and component context."
        ),
        "lag_invariant_left": True,
    },
    {
        "left_surface": "stat_descriptive_node_state_long.tsv",
        "right_surface": "kinetic_temporal_coupling_primary_long.tsv",
        "comparison_keys": ("canonical_component_id", "scenario_canonical", "condition_role"),
        "left_natural_keys": (
            "condition_id",
            "scenario_canonical",
            "condition_role",
            "replicate",
            "canonical_component_id",
            "descriptive_measure_type",
            "timepoint_label",
            "window_label",
        ),
        "right_natural_keys": (
            "condition_id",
            "scenario_canonical",
            "condition_role",
            "replicate",
            "canonical_component_id",
        ),
        "missing_key_dimensions": (
            "condition_id",
            "replicate",
            "descriptive_measure_type",
            "timepoint_label",
            "window_label",
        ),
        "duplicate_origin": "run_max_lag_repetition_across_LAG01_LAG04;multiple_descriptive_measure_rows_per_component",
        "root_cause_kind": "broad_key_omits_condition_replicate_measure_dimensions",
        "join_admissibility": "projection_only",
        "phase02_consumption_mode": "deduplicate_lag_invariant_descriptive_then_project_to_kinetic_component_context",
        "surface_usage_class": "measurement_surface",
        "resolution_notes": (
            "Direct join is forbidden on the broad key. Phase 02 must deduplicate lag-invariant descriptive rows "
            "on the natural key and only project by condition, replicate, and component context."
        ),
        "lag_invariant_left": True,
    },
    {
        "left_surface": "growth_variable_identity_audit.tsv",
        "right_surface": "kinetic_growth_primary_long.tsv",
        "comparison_keys": ("canonical_component_id",),
        "left_alias_map": {"canonical_component_id": "canonical_growth_id"},
        "left_natural_keys": (
            "canonical_growth_id",
            "growth_value_type",
            "source_layer",
            "source_surface",
            "source_column",
            "source_row_key",
        ),
        "right_natural_keys": (
            "condition_id",
            "scenario_canonical",
            "condition_role",
            "replicate",
            "canonical_component_id",
            "value_type",
            "evidence_scope",
        ),
        "missing_key_dimensions": ("not_applicable_policy_surface_non_measurement",),
        "duplicate_origin": "policy_surface_misuse_all_rows_collapse_to_growth_node",
        "root_cause_kind": "policy_surface_misuse_identity_not_measurement",
        "join_admissibility": "policy_lookup_only",
        "phase02_consumption_mode": "identity_policy_lookup_only_do_not_join_as_measurement",
        "surface_usage_class": "identity_policy_surface",
        "resolution_notes": (
            "growth_variable_identity_audit.tsv is a policy surface. It may inform identity compatibility but "
            "must never be joined as measurement evidence to kinetic growth rows."
        ),
        "lag_invariant_left": False,
        "register_non_joinable_left": True,
    },
)

JOIN_OUTPUT_PREFERRED_ORDERS: dict[str, list[str]] = {
    "input_join_key_audit.tsv": [
        "left_surface",
        "right_surface",
        "candidate_keys",
        "normalized_keys",
        "comparison_keys",
        "left_natural_key",
        "right_natural_key",
        "null_rate_by_key",
        "unique_key_rate",
        "many_to_many_risk",
        "match_rate",
        "unmatched_left_count",
        "unmatched_right_count",
        "left_row_count",
        "right_row_count",
        "left_max_multiplicity",
        "right_max_multiplicity",
        "max_cartesian_expansion",
        "missing_key_dimensions",
        "duplicate_origin",
        "join_admissibility",
        "resolution_state",
        "notes",
    ],
    "many_to_many_origin_diagnostic.tsv": [
        "left_surface",
        "right_surface",
        "current_comparison_keys",
        "left_row_count",
        "right_row_count",
        "left_unique_key_rate_current",
        "right_unique_key_rate_current",
        "left_max_multiplicity_current",
        "right_max_multiplicity_current",
        "max_cartesian_expansion_current",
        "left_natural_key",
        "right_natural_key",
        "left_unique_key_rate_natural",
        "right_unique_key_rate_natural",
        "left_max_multiplicity_natural",
        "right_max_multiplicity_natural",
        "missing_key_dimensions",
        "duplicate_origin",
        "root_cause_kind",
        "join_admissibility",
        "resolution_state",
        "notes",
    ],
    "per_surface_natural_key_profile.tsv": [
        "surface_name",
        "natural_key_fields",
        "row_count",
        "unique_key_rate",
        "max_multiplicity",
        "duplicate_key_count",
        "duplicate_origin",
        "notes",
    ],
    "candidate_key_uniqueness_profile.tsv": [
        "pair_id",
        "surface_name",
        "surface_side",
        "key_profile_kind",
        "key_fields",
        "row_count",
        "unique_key_rate",
        "max_multiplicity",
        "duplicate_key_count",
        "null_rate_by_key",
    ],
    "lag_invariant_duplicate_origin_audit.tsv": [
        "surface_name",
        "condition_id",
        "scenario_canonical",
        "condition_role",
        "replicate",
        "canonical_component_id",
        "descriptive_measure_type",
        "timepoint_label",
        "window_label",
        "duplicate_count",
        "distinct_run_max_lag_count",
        "run_max_lag_values",
        "duplicate_origin",
        "dedup_policy",
    ],
    "policy_surface_non_joinable_registry.tsv": [
        "surface_name",
        "source_layer",
        "surface_class",
        "non_joinable_as_measurement",
        "allowed_usage",
        "policy_basis",
        "notes",
    ],
    "join_admissibility_contract.tsv": [
        "left_surface",
        "right_surface",
        "comparison_keys",
        "left_natural_key",
        "right_natural_key",
        "join_admissibility",
        "direct_join_allowed_yes_no",
        "deduplicate_left_before_projection_yes_no",
        "surface_usage_class",
        "resolution_state",
        "notes",
    ],
    "phase02_join_contract.tsv": [
        "left_surface",
        "right_surface",
        "phase02_consumption_mode",
        "direct_join_allowed_yes_no",
        "projection_allowed_yes_no",
        "policy_lookup_allowed_yes_no",
        "required_left_preprocessing",
        "required_right_preprocessing",
        "resolution_state",
        "notes",
    ],
}


def build_input_join_key_audit(
    *,
    phase01a_policy_rows: dict[str, list[dict[str, str]]],
    stat_outputs: dict[str, list[dict[str, object]]],
    kinetic_outputs: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    bundle = build_join_resolution_bundle(
        phase01a_policy_rows=phase01a_policy_rows,
        stat_outputs=stat_outputs,
        kinetic_outputs=kinetic_outputs,
    )
    return bundle["input_join_key_audit.tsv"]


def build_join_resolution_bundle(
    *,
    phase01a_policy_rows: dict[str, list[dict[str, object]]],
    stat_outputs: dict[str, list[dict[str, object]]],
    kinetic_outputs: dict[str, list[dict[str, object]]],
) -> dict[str, list[dict[str, object]]]:
    join_rows: list[dict[str, object]] = [_policy_defined_row(phase01a_policy_rows)]
    diagnostic_rows: list[dict[str, object]] = []
    candidate_profiles: list[dict[str, object]] = []
    lag_duplicate_rows: list[dict[str, object]] = []
    policy_registry_rows: list[dict[str, object]] = []
    join_contract_rows: list[dict[str, object]] = []
    phase02_contract_rows: list[dict[str, object]] = []
    per_surface_profiles: dict[tuple[str, str], dict[str, object]] = {}
    lag_duplicate_markers: set[tuple[object, ...]] = set()

    for spec in PAIR_SPECS:
        left_rows = _surface_rows(
            spec["left_surface"],
            phase01a_policy_rows=phase01a_policy_rows,
            stat_outputs=stat_outputs,
            kinetic_outputs=kinetic_outputs,
        )
        right_rows = _surface_rows(
            spec["right_surface"],
            phase01a_policy_rows=phase01a_policy_rows,
            stat_outputs=stat_outputs,
            kinetic_outputs=kinetic_outputs,
        )
        profile = _profile_pair(spec=spec, left_rows=left_rows, right_rows=right_rows)
        join_rows.append(profile["join_audit_row"])
        diagnostic_rows.append(profile["diagnostic_row"])
        candidate_profiles.extend(profile["candidate_profiles"])
        join_contract_rows.append(profile["join_contract_row"])
        phase02_contract_rows.append(profile["phase02_contract_row"])
        for surface_row in profile["surface_profiles"]:
            marker = (str(surface_row["surface_name"]), str(surface_row["natural_key_fields"]))
            per_surface_profiles.setdefault(marker, surface_row)
        for lag_row in profile["lag_duplicate_rows"]:
            marker = tuple(lag_row.get(name, "") for name in lag_row.keys())
            if marker in lag_duplicate_markers:
                continue
            lag_duplicate_markers.add(marker)
            lag_duplicate_rows.append(lag_row)
        registry_row = profile.get("policy_registry_row")
        if registry_row is not None:
            policy_registry_rows.append(registry_row)

    return {
        "input_join_key_audit.tsv": join_rows,
        "many_to_many_origin_diagnostic.tsv": diagnostic_rows,
        "per_surface_natural_key_profile.tsv": list(per_surface_profiles.values()),
        "candidate_key_uniqueness_profile.tsv": candidate_profiles,
        "lag_invariant_duplicate_origin_audit.tsv": lag_duplicate_rows,
        "policy_surface_non_joinable_registry.tsv": policy_registry_rows,
        "join_admissibility_contract.tsv": join_contract_rows,
        "phase02_join_contract.tsv": phase02_contract_rows,
    }


def join_output_preferred_order(filename: str) -> list[str]:
    return JOIN_OUTPUT_PREFERRED_ORDERS.get(filename, [])


def _policy_defined_row(phase01a_policy_rows: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    policy_row_count = len(phase01a_policy_rows["cross_layer_join_identity_policy.tsv"])
    return {
        "left_surface": "cross_layer_join_identity_policy.tsv",
        "right_surface": "phase01a_policy",
        "candidate_keys": ";".join(FIXED_JOIN_AXES),
        "normalized_keys": ";".join(FIXED_JOIN_AXES),
        "comparison_keys": "policy_defined",
        "left_natural_key": "canonical_component_id;condition_id;scenario_canonical;condition_role;source_layer_left;value_type_left;evidence_scope_left;source_layer_right;value_type_right;evidence_scope_right",
        "right_natural_key": "phase01a_policy_artifact_row",
        "null_rate_by_key": "not_applicable",
        "unique_key_rate": "not_applicable",
        "many_to_many_risk": "policy_defined",
        "match_rate": "not_applicable",
        "unmatched_left_count": 0,
        "unmatched_right_count": 0,
        "policy_artifact_row_count": policy_row_count,
        "left_row_count": policy_row_count,
        "right_row_count": policy_row_count,
        "left_max_multiplicity": 1,
        "right_max_multiplicity": 1,
        "max_cartesian_expansion": 1,
        "missing_key_dimensions": "not_applicable",
        "duplicate_origin": "phase01a_policy_lookup",
        "join_admissibility": "policy_defined",
        "resolution_state": "resolved",
        "notes": "Phase 01B join audit is constrained by immutable Phase 01A policy rows.",
    }


def _profile_pair(
    *,
    spec: dict[str, object],
    left_rows: list[dict[str, object]],
    right_rows: list[dict[str, object]],
) -> dict[str, object]:
    comparison_keys = tuple(spec["comparison_keys"])
    left_alias_map = dict(spec.get("left_alias_map", {}))
    left_broad_keys = tuple(left_alias_map.get(key, key) for key in comparison_keys)
    right_broad_keys = comparison_keys
    left_natural_keys = tuple(spec["left_natural_keys"])
    right_natural_keys = tuple(spec["right_natural_keys"])

    left_broad_counter = Counter(_key(row, left_broad_keys) for row in left_rows)
    right_broad_counter = Counter(_key(row, right_broad_keys) for row in right_rows)
    left_natural_counter = Counter(_key(row, left_natural_keys) for row in left_rows)
    right_natural_counter = Counter(_key(row, right_natural_keys) for row in right_rows)

    left_broad_nonempty = {key for key in left_broad_counter if any(part != "" for part in key)}
    right_broad_nonempty = {key for key in right_broad_counter if any(part != "" for part in key)}
    matched_broad = left_broad_nonempty & right_broad_nonempty
    unresolved = spec["join_admissibility"] not in JOIN_RESOLUTION_VALUES
    max_cartesian = max((left_broad_counter[key] * right_broad_counter[key] for key in matched_broad), default=0)

    join_row = {
        "left_surface": spec["left_surface"],
        "right_surface": spec["right_surface"],
        "candidate_keys": ";".join(FIXED_JOIN_AXES),
        "normalized_keys": ";".join(FIXED_JOIN_AXES),
        "comparison_keys": ";".join(comparison_keys),
        "left_natural_key": ";".join(left_natural_keys),
        "right_natural_key": ";".join(right_natural_keys),
        "null_rate_by_key": ";".join(
            f"{key}:{_null_rate(left_rows, left_alias_map.get(key, key)):.6f}|{_null_rate(right_rows, key):.6f}"
            for key in comparison_keys
        ),
        "unique_key_rate": (
            f"{_unique_key_rate(left_rows, left_broad_keys):.6f}|{_unique_key_rate(right_rows, right_broad_keys):.6f}"
        ),
        "many_to_many_risk": "yes"
        if any(count > 1 for count in left_broad_counter.values()) and any(count > 1 for count in right_broad_counter.values())
        else "no",
        "match_rate": f"{(len(matched_broad) / len(left_broad_nonempty)) if left_broad_nonempty else 0.0:.6f}",
        "unmatched_left_count": len(left_broad_nonempty - right_broad_nonempty),
        "unmatched_right_count": len(right_broad_nonempty - left_broad_nonempty),
        "policy_artifact_row_count": "",
        "left_row_count": len(left_rows),
        "right_row_count": len(right_rows),
        "left_max_multiplicity": _max_count(left_broad_counter),
        "right_max_multiplicity": _max_count(right_broad_counter),
        "max_cartesian_expansion": max_cartesian,
        "missing_key_dimensions": ";".join(spec["missing_key_dimensions"]),
        "duplicate_origin": spec["duplicate_origin"],
        "join_admissibility": spec["join_admissibility"],
        "resolution_state": "unresolved" if unresolved else "resolved",
        "notes": spec["resolution_notes"],
    }

    diagnostic_row = {
        "left_surface": spec["left_surface"],
        "right_surface": spec["right_surface"],
        "current_comparison_keys": ";".join(comparison_keys),
        "left_row_count": len(left_rows),
        "right_row_count": len(right_rows),
        "left_unique_key_rate_current": f"{_unique_key_rate(left_rows, left_broad_keys):.6f}",
        "right_unique_key_rate_current": f"{_unique_key_rate(right_rows, right_broad_keys):.6f}",
        "left_max_multiplicity_current": _max_count(left_broad_counter),
        "right_max_multiplicity_current": _max_count(right_broad_counter),
        "max_cartesian_expansion_current": max_cartesian,
        "left_natural_key": ";".join(left_natural_keys),
        "right_natural_key": ";".join(right_natural_keys),
        "left_unique_key_rate_natural": f"{_unique_key_rate(left_rows, left_natural_keys):.6f}",
        "right_unique_key_rate_natural": f"{_unique_key_rate(right_rows, right_natural_keys):.6f}",
        "left_max_multiplicity_natural": _max_count(left_natural_counter),
        "right_max_multiplicity_natural": _max_count(right_natural_counter),
        "missing_key_dimensions": ";".join(spec["missing_key_dimensions"]),
        "duplicate_origin": spec["duplicate_origin"],
        "root_cause_kind": spec["root_cause_kind"],
        "join_admissibility": spec["join_admissibility"],
        "resolution_state": "unresolved" if unresolved else "resolved",
        "notes": spec["resolution_notes"],
    }

    candidate_profiles = [
        _candidate_profile_row(
            pair_id=_pair_id(spec["left_surface"], spec["right_surface"]),
            surface_name=str(spec["left_surface"]),
            surface_side="left",
            key_profile_kind="current_comparison_key",
            key_fields=left_broad_keys,
            rows=left_rows,
        ),
        _candidate_profile_row(
            pair_id=_pair_id(spec["left_surface"], spec["right_surface"]),
            surface_name=str(spec["right_surface"]),
            surface_side="right",
            key_profile_kind="current_comparison_key",
            key_fields=right_broad_keys,
            rows=right_rows,
        ),
        _candidate_profile_row(
            pair_id=_pair_id(spec["left_surface"], spec["right_surface"]),
            surface_name=str(spec["left_surface"]),
            surface_side="left",
            key_profile_kind="natural_key",
            key_fields=left_natural_keys,
            rows=left_rows,
        ),
        _candidate_profile_row(
            pair_id=_pair_id(spec["left_surface"], spec["right_surface"]),
            surface_name=str(spec["right_surface"]),
            surface_side="right",
            key_profile_kind="natural_key",
            key_fields=right_natural_keys,
            rows=right_rows,
        ),
    ]

    surface_profiles = [
        _surface_profile_row(
            surface_name=str(spec["left_surface"]),
            natural_key_fields=left_natural_keys,
            rows=left_rows,
            duplicate_origin=str(spec["duplicate_origin"]) if spec.get("lag_invariant_left") else "none",
            notes="Left surface natural key profile.",
        ),
        _surface_profile_row(
            surface_name=str(spec["right_surface"]),
            natural_key_fields=right_natural_keys,
            rows=right_rows,
            duplicate_origin="none",
            notes="Right surface natural key profile.",
        ),
    ]

    lag_duplicate_rows = []
    if spec.get("lag_invariant_left"):
        lag_duplicate_rows = _lag_duplicate_origin_rows(
            surface_name=str(spec["left_surface"]),
            rows=left_rows,
            natural_key_fields=left_natural_keys,
        )

    join_contract_row = {
        "left_surface": spec["left_surface"],
        "right_surface": spec["right_surface"],
        "comparison_keys": ";".join(comparison_keys),
        "left_natural_key": ";".join(left_natural_keys),
        "right_natural_key": ";".join(right_natural_keys),
        "join_admissibility": spec["join_admissibility"],
        "direct_join_allowed_yes_no": "yes" if spec["join_admissibility"] == "joinable" else "no",
        "deduplicate_left_before_projection_yes_no": "yes" if spec.get("lag_invariant_left") else "no",
        "surface_usage_class": spec["surface_usage_class"],
        "resolution_state": "unresolved" if unresolved else "resolved",
        "notes": spec["resolution_notes"],
    }

    phase02_contract_row = {
        "left_surface": spec["left_surface"],
        "right_surface": spec["right_surface"],
        "phase02_consumption_mode": spec["phase02_consumption_mode"],
        "direct_join_allowed_yes_no": "yes" if spec["join_admissibility"] == "joinable" else "no",
        "projection_allowed_yes_no": "yes" if spec["join_admissibility"] == "projection_only" else "no",
        "policy_lookup_allowed_yes_no": "yes" if spec["join_admissibility"] == "policy_lookup_only" else "no",
        "required_left_preprocessing": (
            "deduplicate_on_natural_key_before_projection" if spec.get("lag_invariant_left") else "none"
        ),
        "required_right_preprocessing": "none",
        "resolution_state": "unresolved" if unresolved else "resolved",
        "notes": spec["resolution_notes"],
    }

    policy_registry_row = None
    if spec.get("register_non_joinable_left"):
        policy_registry_row = {
            "surface_name": spec["left_surface"],
            "source_layer": "phase01a_policy",
            "surface_class": "identity_policy_surface",
            "non_joinable_as_measurement": "yes",
            "allowed_usage": "policy_lookup_only",
            "policy_basis": "growth_variable_identity_audit_rows_are_identity_contract_not_measurement_evidence",
            "notes": spec["resolution_notes"],
        }

    return {
        "join_audit_row": join_row,
        "diagnostic_row": diagnostic_row,
        "candidate_profiles": candidate_profiles,
        "surface_profiles": surface_profiles,
        "lag_duplicate_rows": lag_duplicate_rows,
        "policy_registry_row": policy_registry_row,
        "join_contract_row": join_contract_row,
        "phase02_contract_row": phase02_contract_row,
    }


def _surface_rows(
    surface_name: str,
    *,
    phase01a_policy_rows: dict[str, list[dict[str, object]]],
    stat_outputs: dict[str, list[dict[str, object]]],
    kinetic_outputs: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    if surface_name in phase01a_policy_rows:
        return phase01a_policy_rows[surface_name]
    if surface_name in stat_outputs:
        return stat_outputs[surface_name]
    if surface_name in kinetic_outputs:
        return kinetic_outputs[surface_name]
    raise KeyError(f"Unknown surface {surface_name!r}")


def _candidate_profile_row(
    *,
    pair_id: str,
    surface_name: str,
    surface_side: str,
    key_profile_kind: str,
    key_fields: tuple[str, ...],
    rows: list[dict[str, object]],
) -> dict[str, object]:
    counter = Counter(_key(row, key_fields) for row in rows)
    duplicate_key_count = sum(1 for count in counter.values() if count > 1)
    return {
        "pair_id": pair_id,
        "surface_name": surface_name,
        "surface_side": surface_side,
        "key_profile_kind": key_profile_kind,
        "key_fields": ";".join(key_fields),
        "row_count": len(rows),
        "unique_key_rate": f"{_unique_key_rate(rows, key_fields):.6f}",
        "max_multiplicity": _max_count(counter),
        "duplicate_key_count": duplicate_key_count,
        "null_rate_by_key": ";".join(f"{field}:{_null_rate(rows, field):.6f}" for field in key_fields),
    }


def _surface_profile_row(
    *,
    surface_name: str,
    natural_key_fields: tuple[str, ...],
    rows: list[dict[str, object]],
    duplicate_origin: str,
    notes: str,
) -> dict[str, object]:
    counter = Counter(_key(row, natural_key_fields) for row in rows)
    duplicate_key_count = sum(1 for count in counter.values() if count > 1)
    return {
        "surface_name": surface_name,
        "natural_key_fields": ";".join(natural_key_fields),
        "row_count": len(rows),
        "unique_key_rate": f"{_unique_key_rate(rows, natural_key_fields):.6f}",
        "max_multiplicity": _max_count(counter),
        "duplicate_key_count": duplicate_key_count,
        "duplicate_origin": duplicate_origin,
        "notes": notes,
    }


def _lag_duplicate_origin_rows(
    *,
    surface_name: str,
    rows: list[dict[str, object]],
    natural_key_fields: tuple[str, ...],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(_key(row, natural_key_fields), []).append(row)
    results: list[dict[str, object]] = []
    for natural_key, members in grouped.items():
        if len(members) <= 1:
            continue
        run_lags = sorted({str(member.get("run_max_lag", "")) for member in members if str(member.get("run_max_lag", "")) != ""})
        if not run_lags:
            continue
        exemplar = members[0]
        results.append(
            {
                "surface_name": surface_name,
                "condition_id": exemplar.get("condition_id", ""),
                "scenario_canonical": exemplar.get("scenario_canonical", ""),
                "condition_role": exemplar.get("condition_role", ""),
                "replicate": exemplar.get("replicate", ""),
                "canonical_component_id": exemplar.get("canonical_component_id", ""),
                "descriptive_measure_type": exemplar.get("descriptive_measure_type", ""),
                "timepoint_label": exemplar.get("timepoint_label", ""),
                "window_label": exemplar.get("window_label", ""),
                "duplicate_count": len(members),
                "distinct_run_max_lag_count": len(run_lags),
                "run_max_lag_values": ";".join(run_lags),
                "duplicate_origin": "lag_invariant_descriptive_surface_repeated_for_each_run_max_lag",
                "dedup_policy": "deduplicate_on_natural_key_before_phase02_projection",
            }
        )
    return results


def _pair_id(left_surface: object, right_surface: object) -> str:
    return f"{left_surface}->{right_surface}"


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


def _max_count(counter: Counter[tuple[str, ...]]) -> int:
    return max(counter.values(), default=0)
