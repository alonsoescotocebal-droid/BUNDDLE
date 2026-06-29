"""Validation helpers for Phase03A probabilistic calibration artifacts."""

from __future__ import annotations

from pathlib import Path

from ..config import PHASE03A_APPROVED_COMPLETION_STATE, PHASE03A_FORBIDDEN_OUTPUTS


REQUIRED_POSTERIOR_COLUMNS = {
    "relation_anchor_id",
    "target_component_id",
    "perturbator_component_id",
    "scenario_canonical",
    "condition_role",
    "condition_id",
    "replicate",
    "window_label",
    "run_max_lag",
    "edge_lag",
    "calibration_route",
    "calibration_status",
    "qc_blocker_status",
    "semantic_compatibility_status",
    "p_positive_support",
    "p_negative_support",
    "p_ambiguous_or_mixed",
    "p_insufficient_or_uninformative",
    "posterior_state_argmax",
    "posterior_entropy",
    "probability_limitations_flag",
    "not_causal_probability_yes_no",
    "not_qa_answer_yes_no",
    "not_network_topology_yes_no",
    "not_final_decision_yes_no",
    "trace_id",
}
ALLOWED_CALIBRATION_ROUTES = {
    "empirical_rank_by_run_max_lag",
    "empirical_rank_pooled_lags",
    "conservative_logistic_fallback",
    "missing_or_invalid_q_value",
}


def build_phase03a_validation_summary(
    *,
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    output_root_boundary_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    manifest: dict[str, object],
    preflight_rows: list[dict[str, object]],
    method_manifest: dict[str, object],
    temporal_calibration_rows: list[dict[str, object]],
    probability_calibration_audit_rows: list[dict[str, object]],
    multilag_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
    semantic_registry_rows: list[dict[str, object]],
    semantic_compatibility_rows: list[dict[str, object]],
    probability_tensor_rows: list[dict[str, object]],
    posterior_rows: list[dict[str, object]],
    forbidden_scan_rows: list[dict[str, object]],
    empty_or_absent_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    preflight_index = {str(row.get("check_id", "")): row for row in preflight_rows}

    boundary = output_root_boundary_rows[0] if output_root_boundary_rows else {}
    boundary_ok = (
        boundary.get("repo_conflict") == "no"
        and boundary.get("allowed_root_check") == "pass"
        and boundary.get("decision") == "allow"
    )
    rows.append(
        _summary_row(
            "output_root_external_boundary",
            "PASS" if boundary_ok else "FAIL",
            "info" if boundary_ok else "error",
            "audit/output_root_boundary_audit.tsv",
            str(runtime_root),
            (
                f"repo_conflict={boundary.get('repo_conflict', '')};"
                f"allowed_root_check={boundary.get('allowed_root_check', '')};"
                f"decision={boundary.get('decision', '')}"
            ),
        )
    )

    contamination_failures = [row for row in repo_contamination_rows if str(row.get("status", "")).startswith("fail_")]
    contamination_pass = any(row.get("status") == "pass_no_new_repo_runtime_outputs" for row in repo_contamination_rows)
    repo_ok = not contamination_failures and contamination_pass
    rows.append(
        _summary_row(
            "repo_no_contamination",
            "PASS" if repo_ok else "FAIL",
            "info" if repo_ok else "error",
            "audit/repo_contamination_audit.tsv",
            "repo_snapshot_delta",
            f"failures={len(contamination_failures)};pass_marker={contamination_pass}",
        )
    )

    manifest_ok = (
        manifest.get("phase") == "phase03a"
        and manifest.get("phase_status") == "phase03a_probabilistic_calibration_complete_waiting_for_phase03b_plan"
        and manifest.get("pipeline_global_status") == "not_closed"
        and manifest.get("final_go_no_go") == "not_applicable_for_phase03a"
        and manifest.get("not_qa22_yes_no") == "yes"
        and manifest.get("not_network_topology_yes_no") == "yes"
        and manifest.get("not_global_closure_yes_no") == "yes"
        and manifest.get("posterior_not_causal_probability_yes_no") == "yes"
    )
    rows.append(
        _summary_row(
            "manifest_phase03a_state",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase_state",
            (
                f"phase={manifest.get('phase')};phase_status={manifest.get('phase_status')};"
                f"pipeline_global_status={manifest.get('pipeline_global_status')};"
                f"final_go_no_go={manifest.get('final_go_no_go')}"
            ),
        )
    )

    rows.append(_mirror_preflight(preflight_index, "phase02_manifest_state_valid", "phase02_runtime_manifest_valid"))
    rows.append(_mirror_preflight(preflight_index, "phase02_validation_clean", "phase02_validation_clean"))
    rows.append(_mirror_preflight(preflight_index, "phase03a_required_inputs_present", "phase03a_required_inputs_present"))
    rows.append(_mirror_preflight(preflight_index, "phase02_forbidden_outputs_absent", "phase02_forbidden_outputs_absent"))
    rows.append(_mirror_preflight(preflight_index, "relation_evidence_tensor_present", "relation_evidence_tensor_present"))
    rows.append(_mirror_preflight(preflight_index, "relation_evidence_tensor_not_posterior", "relation_evidence_tensor_not_posterior"))
    rows.append(_mirror_preflight(preflight_index, "no_raw_roots_consumed", "no_raw_roots_consumed"))
    rows.append(_mirror_preflight(preflight_index, "no_phase01b_runtime_direct_consumption", "no_phase01b_runtime_direct_consumption"))
    rows.append(_mirror_preflight(preflight_index, "run_max_lag_edge_lag_preserved", "run_max_lag_edge_lag_preserved"))
    rows.append(_mirror_preflight(preflight_index, "no_global_lag_priority", "no_global_lag_priority"))

    kinetic_real_only_ok = all(row.get("branch", "") in {"", "real_only"} for row in kinetic_rows if row.get("relation_anchor_id"))
    rows.append(
        _summary_row(
            "kinetic_real_only_only",
            "PASS" if kinetic_real_only_ok else "FAIL",
            "info" if kinetic_real_only_ok else "error",
            "data/kinetic_likelihood_surface.tsv",
            "branch",
            f"row_count={len(kinetic_rows)}",
        )
    )

    real_plus_absent = all(row.get("branch", "") != "real_plus_interpolated" for row in kinetic_rows if row.get("relation_anchor_id"))
    rows.append(
        _summary_row(
            "real_plus_interpolated_absent_from_kinetic_likelihood",
            "PASS" if real_plus_absent else "FAIL",
            "info" if real_plus_absent else "error",
            "data/kinetic_likelihood_surface.tsv",
            "branch",
            "none_present" if real_plus_absent else "real_plus_interpolated_detected",
        )
    )

    route_declared = bool(temporal_calibration_rows) and all(row.get("calibration_route") for row in temporal_calibration_rows)
    rows.append(
        _summary_row(
            "calibration_route_declared",
            "PASS" if route_declared else "FAIL",
            "info" if route_declared else "error",
            "data/temporal_pcmci_calibration_surface.tsv",
            "calibration_route",
            f"row_count={len(temporal_calibration_rows)}",
        )
    )

    route_justified = bool(temporal_calibration_rows) and all(
        row.get("calibration_route") in ALLOWED_CALIBRATION_ROUTES
        and (
            row.get("calibration_route") != "conservative_logistic_fallback"
            or str(row.get("fallback_reason", "")) != ""
        )
        for row in temporal_calibration_rows
    )
    rows.append(
        _summary_row(
            "empirical_or_fallback_route_justified",
            "PASS" if route_justified else "FAIL",
            "info" if route_justified else "error",
            "data/temporal_pcmci_calibration_surface.tsv",
            "calibration_route",
            f"routes={';'.join(sorted({str(row.get('calibration_route', '')) for row in temporal_calibration_rows}))}",
        )
    )

    method_manifest_ok = bool(method_manifest) and method_manifest.get("phase") == "phase03a"
    rows.append(
        _summary_row(
            "probability_method_manifest_exists",
            "PASS" if method_manifest_ok else "FAIL",
            "info" if method_manifest_ok else "error",
            "data/probability_method_manifest.json",
            "method_manifest",
            str(method_manifest.get("method_version", "")),
        )
    )

    probability_tensor_not_posterior = bool(probability_tensor_rows) and all(
        row.get("not_posterior_yes_no") == "yes" for row in probability_tensor_rows
    )
    rows.append(
        _summary_row(
            "relation_probability_evidence_tensor_not_posterior",
            "PASS" if probability_tensor_not_posterior else "FAIL",
            "info" if probability_tensor_not_posterior else "error",
            "data/relation_probability_evidence_tensor.tsv",
            "not_posterior_yes_no",
            f"row_count={len(probability_tensor_rows)}",
        )
    )

    calibration_expected_counts = _counts_by_run_max_lag(temporal_calibration_rows)
    calibration_audit_counts = {
        str(row.get("calibration_group", "")): int(float(row.get("row_count", 0) or 0))
        for row in probability_calibration_audit_rows
        if row.get("audit_scope") == "run_max_lag"
    }
    calibration_row_counts_match = (
        bool(temporal_calibration_rows)
        and calibration_expected_counts == calibration_audit_counts
    )
    rows.append(
        _summary_row(
            "probability_calibration_audit_row_counts_match",
            "PASS" if calibration_row_counts_match else "FAIL",
            "info" if calibration_row_counts_match else "error",
            "data/probability_calibration_audit.tsv",
            "run_max_lag",
            f"expected={calibration_expected_counts};actual={calibration_audit_counts}",
        )
    )

    rows.append(
        _summary_row(
            "semantic_polarity_registry_exists",
            "PASS" if bool(semantic_registry_rows) else "FAIL",
            "info" if semantic_registry_rows else "error",
            "data/semantic_polarity_registry.tsv",
            "semantic_registry_rows",
            f"row_count={len(semantic_registry_rows)}",
        )
    )
    rows.append(
        _summary_row(
            "semantic_compatibility_surface_exists",
            "PASS" if bool(semantic_compatibility_rows) else "FAIL",
            "info" if semantic_compatibility_rows else "error",
            "data/semantic_compatibility_surface.tsv",
            "semantic_compatibility_rows",
            f"row_count={len(semantic_compatibility_rows)}",
        )
    )

    multilag_ok = bool(multilag_rows) and all(
        row.get("run_max_lag") != ""
        and row.get("edge_lag") != ""
        and row.get("no_global_lag_priority_yes_no") == "yes"
        for row in multilag_rows
    )
    rows.append(
        _summary_row(
            "multilag_profile_preserved",
            "PASS" if multilag_ok else "FAIL",
            "info" if multilag_ok else "error",
            "data/multilag_temporal_profile_surface.tsv",
            "multilag_rows",
            f"row_count={len(multilag_rows)}",
        )
    )

    has_legitimate_yield_absence = any(
        row.get("source_surface") == "kinetic_yield_evidence_intake.tsv" and row.get("legitimate_absence_yes_no") == "yes"
        for row in kinetic_rows
    )
    has_real_yield_rows = any(
        row.get("source_surface") == "kinetic_yield_evidence_intake.tsv" and row.get("relation_anchor_id")
        for row in kinetic_rows
    )
    yield_ok = has_real_yield_rows or has_legitimate_yield_absence
    rows.append(
        _summary_row(
            "yield_absence_only_if_legitimate",
            "PASS" if yield_ok else "FAIL",
            "info" if yield_ok else "error",
            "data/kinetic_likelihood_surface.tsv",
            "kinetic_yield",
            "yield_rows_present" if has_real_yield_rows else "legitimate_absence" if has_legitimate_yield_absence else "no_yield_rows_without_legitimate_absence",
        )
    )

    q_values_not_direct_probability = bool(temporal_calibration_rows) and all(
        0.0 <= float(row.get("p_temporal_signal_support", 0.0) or 0.0) <= 1.0
        for row in temporal_calibration_rows
    )
    rows.append(
        _summary_row(
            "q_values_not_direct_probability",
            "PASS" if q_values_not_direct_probability else "FAIL",
            "info" if q_values_not_direct_probability else "error",
            "data/temporal_pcmci_calibration_surface.tsv",
            "p_temporal_signal_support",
            "Temporal support probabilities are calibrated internal support masses, not raw q-values.",
        )
    )

    posterior_columns_complete = bool(posterior_rows) and REQUIRED_POSTERIOR_COLUMNS.issubset(set(posterior_rows[0].keys()))
    rows.append(
        _summary_row(
            "posterior_state_columns_complete",
            "PASS" if posterior_columns_complete else "FAIL",
            "info" if posterior_columns_complete else "error",
            "data/posterior_relation_state.tsv",
            "posterior_columns",
            "all_required_columns_present" if posterior_columns_complete else ";".join(sorted(REQUIRED_POSTERIOR_COLUMNS - set(posterior_rows[0].keys() if posterior_rows else []))),
        )
    )

    probabilities_in_range = bool(posterior_rows) and all(
        0.0 <= float(row[field]) <= 1.0
        for row in posterior_rows
        for field in (
            "p_positive_support",
            "p_negative_support",
            "p_ambiguous_or_mixed",
            "p_insufficient_or_uninformative",
        )
    )
    rows.append(
        _summary_row(
            "posterior_probabilities_between_zero_and_one",
            "PASS" if probabilities_in_range else "FAIL",
            "info" if probabilities_in_range else "error",
            "data/posterior_relation_state.tsv",
            "posterior_probability_range",
            f"row_count={len(posterior_rows)}",
        )
    )

    probabilities_sum_to_one = bool(posterior_rows) and all(
        abs(
            float(row["p_positive_support"])
            + float(row["p_negative_support"])
            + float(row["p_ambiguous_or_mixed"])
            + float(row["p_insufficient_or_uninformative"])
            - 1.0
        )
        <= 1e-6
        for row in posterior_rows
    )
    rows.append(
        _summary_row(
            "posterior_probabilities_sum_to_one",
            "PASS" if probabilities_sum_to_one else "FAIL",
            "info" if probabilities_sum_to_one else "error",
            "data/posterior_relation_state.tsv",
            "posterior_probability_sum",
            f"row_count={len(posterior_rows)}",
        )
    )

    rows.append(_posterior_flag_check(posterior_rows, "not_causal_probability_yes_no", "posterior_not_causal_probability"))
    rows.append(_posterior_flag_check(posterior_rows, "not_qa_answer_yes_no", "posterior_not_qa_answer"))
    rows.append(_posterior_flag_check(posterior_rows, "not_network_topology_yes_no", "posterior_not_topology"))
    rows.append(_posterior_flag_check(posterior_rows, "not_final_decision_yes_no", "posterior_not_final_decision"))

    forbidden_absent = all(row.get("present_yes_no") == "no" for row in forbidden_scan_rows)
    rows.append(
        _summary_row(
            "forbidden_outputs_absent",
            "PASS" if forbidden_absent else "FAIL",
            "info" if forbidden_absent else "error",
            "data/phase03_forbidden_output_scan.tsv",
            "forbidden_outputs",
            "none_present" if forbidden_absent else ";".join(
                str(row.get("relative_path", "")) for row in forbidden_scan_rows if row.get("present_yes_no") == "yes"
            ),
        )
    )

    deferred_outputs = {"audit/phase03_validation_summary.tsv"}
    missing_required = [
        relative_path
        for relative_path in required_outputs
        if relative_path not in deferred_outputs
        and not (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    rows.append(
        _summary_row(
            "required_artifacts_exist",
            "PASS" if not missing_required else "FAIL",
            "info" if not missing_required else "error",
            "runtime_root",
            "required_outputs",
            "none_missing" if not missing_required else ";".join(sorted(missing_required)),
        )
    )

    probability_audit_exists = bool(empty_or_absent_rows)
    rows.append(
        _summary_row(
            "phase03_empty_or_absent_probability_audit_exists",
            "PASS" if probability_audit_exists else "FAIL",
            "info" if probability_audit_exists else "error",
            "data/phase03_empty_or_absent_probability_audit.tsv",
            "probability_audit_rows",
            f"row_count={len(empty_or_absent_rows)}",
        )
    )

    status_complete = manifest.get("phase03a_completion_decision") == PHASE03A_APPROVED_COMPLETION_STATE
    rows.append(
        _summary_row(
            "phase03a_repaired_and_phase03b_plan_allowed",
            "PASS" if status_complete else "FAIL",
            "info" if status_complete else "error",
            "manifest/runtime_manifest.json",
            "phase03a_completion_decision",
            str(manifest.get("phase03a_completion_decision", "")),
        )
    )

    rows.extend(preflight_rows)
    return rows


def build_phase03a_forbidden_scan_rows(runtime_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in PHASE03A_FORBIDDEN_OUTPUTS:
        if "*" in relative_path:
            matches = list(runtime_root.glob(relative_path.replace("/", "\\")))
            present = bool(matches)
            details = ";".join(str(match.relative_to(runtime_root)).replace("\\", "/") for match in matches)
        else:
            present = (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
            details = relative_path if present else ""
        rows.append(
            {
                "relative_path": relative_path,
                "present_yes_no": "yes" if present else "no",
                "status": "fail_forbidden_output_present" if present else "pass_forbidden_output_absent",
                "details": details,
            }
        )
    return rows


def _mirror_preflight(
    preflight_index: dict[str, dict[str, object]],
    source_check_id: str,
    output_check_id: str,
) -> dict[str, object]:
    row = preflight_index.get(source_check_id, {})
    status = "PASS" if row.get("status") == "PASS" else "FAIL"
    severity = "info" if status == "PASS" else "error"
    return _summary_row(
        output_check_id,
        status,
        severity,
        str(row.get("source_surface", "")),
        str(row.get("source_row_key", "")),
        str(row.get("details", "")),
    )


def _posterior_flag_check(
    posterior_rows: list[dict[str, object]],
    field: str,
    check_id: str,
) -> dict[str, object]:
    ok = bool(posterior_rows) and all(row.get(field) == "yes" for row in posterior_rows)
    return _summary_row(
        check_id,
        "PASS" if ok else "FAIL",
        "info" if ok else "error",
        "data/posterior_relation_state.tsv",
        field,
        f"row_count={len(posterior_rows)}",
    )


def _counts_by_run_max_lag(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        lag = str(row.get("run_max_lag", ""))
        counts[lag] = counts.get(lag, 0) + 1
    return counts


def _summary_row(
    check_id: str,
    status: str,
    severity: str,
    source_surface: str,
    source_row_key: str,
    details: str,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "status": status,
        "severity": severity,
        "source_surface": source_surface,
        "source_row_key": source_row_key,
        "details": details,
    }
