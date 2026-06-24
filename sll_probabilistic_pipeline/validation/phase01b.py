"""Validation helpers for Phase 01B artifacts."""

from __future__ import annotations

from pathlib import Path


FORBIDDEN_PHASE02_PHASE03_OUTPUTS = (
    "data/relation_evidence_tensor.tsv",
    "data/empirical_null_calibration_summary.tsv",
    "data/local_fdr_signal_probability.tsv",
    "data/bayes_factor_calibration_audit.tsv",
    "data/pcmci_lag_specific_evidence.tsv",
    "data/pcmci_lag_persistence_surface.tsv",
    "data/pcmci_lag_conflict_audit.tsv",
    "data/kinetic_likelihood_surface.tsv",
    "data/conditioned_pair_probability_surface.tsv",
    "data/descriptive_probability_surface.tsv",
    "data/posterior_relation_state.tsv",
    "data/posterior_relation_state.json",
    "data/score_global_local_surface.tsv",
    "data/probabilistic_question_answer_matrix.tsv",
    "data/probabilistic_question_answer_matrix.json",
    "data/network_topology_summary.tsv",
    "data/network_topology_summary.json",
    "data/final_machine_readable_consistency_audit.tsv",
    "data/final_static_release_decision.json",
)


def build_phase01b_validation_summary(
    *,
    validation_rows: list[dict[str, object]],
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    discovered_lags: list[int],
    output_root_boundary_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    manifest: dict[str, object],
    phase01a_carry_forward_rows: list[dict[str, object]],
    availability_rows: list[dict[str, object]],
    join_audit_rows: list[dict[str, object]],
    stat_outputs: dict[str, list[dict[str, object]]],
    kinetic_outputs: dict[str, list[dict[str, object]]],
    empty_audit_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

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
            f"repo_conflict={boundary.get('repo_conflict', '')};allowed_root_check={boundary.get('allowed_root_check', '')};decision={boundary.get('decision', '')}",
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
        manifest.get("phase") == "phase01b"
        and manifest.get("phase_status") == "phase01b_complete_waiting_for_phase02_approval"
        and manifest.get("pipeline_global_status") == "not_closed"
        and manifest.get("final_go_no_go") == "not_applicable_for_phase01b"
    )
    rows.append(
        _summary_row(
            "manifest_phase01b_state",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase_state",
            (
                f"phase={manifest.get('phase')};phase_status={manifest.get('phase_status')};"
                f"pipeline_global_status={manifest.get('pipeline_global_status')};final_go_no_go={manifest.get('final_go_no_go')}"
            ),
        )
    )

    forbidden_found = [
        relative_path
        for relative_path in FORBIDDEN_PHASE02_PHASE03_OUTPUTS
        if (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    report_dir = runtime_root / "report"
    if report_dir.exists():
        forbidden_found.extend(str(path.relative_to(runtime_root)).replace("\\", "/") for path in report_dir.rglob("*") if path.is_file())
    no_phase02 = not forbidden_found
    rows.append(
        _summary_row(
            "no_phase02_outputs_present",
            "PASS" if no_phase02 else "FAIL",
            "info" if no_phase02 else "error",
            "runtime_root",
            "phase_scope",
            "none" if no_phase02 else ";".join(sorted(forbidden_found)),
        )
    )

    carry_forward_ok = (
        len(phase01a_carry_forward_rows) == 5
        and all(row.get("status") == "present_and_usable" for row in phase01a_carry_forward_rows)
        and all(row.get("immutable_policy_yes_no") == "yes" for row in phase01a_carry_forward_rows)
    )
    rows.append(
        _summary_row(
            "phase01a_policy_carry_forward_immutable",
            "PASS" if carry_forward_ok else "FAIL",
            "info" if carry_forward_ok else "error",
            "data/phase01a_policy_carry_forward_audit.tsv",
            "phase01a_policy_artifacts",
            f"row_count={len(phase01a_carry_forward_rows)}",
        )
    )

    lag_coverage_ok = discovered_lags == [1, 2, 3, 4]
    rows.append(
        _summary_row(
            "statistical_lag01_lag04_coverage",
            "PASS" if lag_coverage_ok else "FAIL",
            "info" if lag_coverage_ok else "error",
            "data/stat_pcmci_edge_long.tsv",
            "run_max_lag",
            f"discovered_lags={discovered_lags}",
        )
    )

    edge_rows = stat_outputs["stat_pcmci_edge_long.tsv"]
    run_edge_fields_ok = bool(edge_rows) and all(row.get("run_max_lag", "") != "" and row.get("edge_lag", "") != "" for row in edge_rows)
    run_edge_separation_ok = run_edge_fields_ok and any(str(row["run_max_lag"]) != str(row["edge_lag"]) for row in edge_rows)
    rows.append(
        _summary_row(
            "run_max_lag_edge_lag_separation",
            "PASS" if run_edge_separation_ok else "FAIL",
            "info" if run_edge_separation_ok else "error",
            "data/stat_pcmci_edge_long.tsv",
            "run_max_lag|edge_lag",
            (
                f"row_count={len(edge_rows)};fields_present={run_edge_fields_ok};"
                f"separate_values_present={run_edge_separation_ok}"
            ),
        )
    )

    edge_lag_details = [row for row in validation_rows if row.get("check_id") == "edge_lag_le_run_max_lag_detail"]
    edge_lag_failures = [row for row in edge_lag_details if row.get("status") == "FAIL"]
    rows.append(
        _summary_row(
            "edge_lag_le_run_max_lag",
            "PASS" if not edge_lag_failures else "FAIL",
            "info" if not edge_lag_failures else "error",
            "data/stat_pcmci_edge_long.tsv",
            "edge_lag<=run_max_lag",
            f"detail_rows={len(edge_lag_details)};failures={len(edge_lag_failures)}",
        )
    )

    provenance_rows = stat_outputs["stat_dense_data_provenance_long.tsv"]
    provenance_present = bool(provenance_rows)
    rows.append(
        _summary_row(
            "stat_dense_provenance_present",
            "PASS" if provenance_present else "FAIL",
            "info" if provenance_present else "error",
            "data/stat_dense_data_provenance_long.tsv",
            "provenance_rows",
            f"row_count={len(provenance_rows)}",
        )
    )

    dense_related = [row for row in provenance_rows if row.get("provenance_kind") in {"dense_input", "dense_interpolated"}]
    dense_flags = [str(row.get("is_interpolated", "")) for row in dense_related if str(row.get("is_interpolated", "")) != ""]
    dense_positive = any(flag.lower() in {"1", "yes", "true"} for flag in dense_flags)
    dense_flags_ok = bool(dense_flags) and dense_positive
    rows.append(
        _summary_row(
            "stat_dense_interpolation_flags_preserved",
            "PASS" if dense_flags_ok else "FAIL",
            "info" if dense_flags_ok else "error",
            "data/stat_dense_data_provenance_long.tsv",
            "is_interpolated",
            f"dense_related_rows={len(dense_related)};flagged_rows={len(dense_flags)};positive_interpolated={dense_positive}",
        )
    )

    direct_trace_ok = bool(provenance_rows) and all(
        row.get("direct_read_yes_no") == "yes"
        and row.get("source_path")
        and row.get("source_surface")
        and row.get("source_row_key")
        and row.get("trace_id")
        for row in provenance_rows
    )
    rows.append(
        _summary_row(
            "stat_dense_direct_read_trace_present",
            "PASS" if direct_trace_ok else "FAIL",
            "info" if direct_trace_ok else "error",
            "data/stat_dense_data_provenance_long.tsv",
            "source_path|source_surface|source_row_key|trace_id",
            f"row_count={len(provenance_rows)}",
        )
    )

    primary_surface_names = (
        "kinetic_growth_primary_long.tsv",
        "kinetic_rate_primary_long.tsv",
        "kinetic_temporal_coupling_primary_long.tsv",
        "kinetic_yield_primary_long.tsv",
    )
    primary_rows = [row for name in primary_surface_names for row in kinetic_outputs[name]]
    primary_real_only_ok = all(row.get("branch") == "real_only" for row in primary_rows)
    rows.append(
        _summary_row(
            "kinetic_primary_real_only_only",
            "PASS" if primary_real_only_ok else "FAIL",
            "info" if primary_real_only_ok else "error",
            "data/kinetic_*_primary_long.tsv",
            "branch",
            f"primary_row_count={len(primary_rows)}",
        )
    )

    disabled_inventory_rows = kinetic_outputs["kinetic_disabled_branch_inventory.tsv"]
    disabled_inventory_ok = bool(disabled_inventory_rows) and all(
        row.get("branch") == "real_plus_interpolated" and row.get("status") == "excluded_by_canonical_rule"
        for row in disabled_inventory_rows
    )
    no_disabled_in_primary = all(row.get("branch") != "real_plus_interpolated" for row in primary_rows)
    disabled_ok = disabled_inventory_ok and no_disabled_in_primary
    rows.append(
        _summary_row(
            "kinetic_real_plus_interpolated_disabled_inventory",
            "PASS" if disabled_ok else "FAIL",
            "info" if disabled_ok else "error",
            "data/kinetic_disabled_branch_inventory.tsv",
            "real_plus_interpolated",
            f"inventory_rows={len(disabled_inventory_rows)};primary_has_disabled_branch={not no_disabled_in_primary}",
        )
    )

    yield_empty_row = next(
        (row for row in empty_audit_rows if row.get("source_surface") == "95_audit/yield_pairs_handoff.tsv"),
        None,
    )
    yield_empty_ok = yield_empty_row is not None and yield_empty_row.get("empty_status") == "empty_legitimate"
    rows.append(
        _summary_row(
            "kinetic_yield_empty_legitimate",
            "PASS" if yield_empty_ok else "FAIL",
            "info" if yield_empty_ok else "error",
            "data/input_empty_surface_audit.tsv",
            "95_audit/yield_pairs_handoff.tsv",
            yield_empty_row.get("basis", "") if yield_empty_row else "yield empty audit row missing",
        )
    )

    required_availability_rows = [row for row in availability_rows if row.get("required_yes_no") == "yes"]
    required_missing = [
        row for row in required_availability_rows if row.get("status") not in {"available", "empty_legitimate"}
    ]
    rows.append(
        _summary_row(
            "input_surface_availability_no_missing_required",
            "PASS" if not required_missing else "FAIL",
            "info" if not required_missing else "error",
            "data/input_surface_availability_audit.tsv",
            "required_surfaces",
            f"required_rows={len(required_availability_rows)};problem_rows={len(required_missing)}",
        )
    )

    join_exists = bool(join_audit_rows)
    rows.append(
        _summary_row(
            "join_audit_exists",
            "PASS" if join_exists else "FAIL",
            "info" if join_exists else "error",
            "data/input_join_key_audit.tsv",
            "join_profile_rows",
            f"row_count={len(join_audit_rows)}",
        )
    )

    many_to_many_count = sum(1 for row in join_audit_rows if row.get("many_to_many_risk") == "yes")
    if not join_exists:
        join_risk_status = "FAIL"
        join_risk_severity = "error"
    elif many_to_many_count > 0:
        join_risk_status = "WARN"
        join_risk_severity = "warning"
    else:
        join_risk_status = "PASS"
        join_risk_severity = "info"
    rows.append(
        _summary_row(
            "join_many_to_many_risk_profiled_not_joined",
            join_risk_status,
            join_risk_severity,
            "data/input_join_key_audit.tsv",
            "many_to_many_risk",
            f"rows_with_risk={many_to_many_count};profiling_only_phase01b=yes",
        )
    )

    missing_required_artifacts = [
        relative_path
        for relative_path in required_outputs
        if not (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    artifacts_ok = not missing_required_artifacts
    rows.append(
        _summary_row(
            "required_artifacts_exist",
            "PASS" if artifacts_ok else "FAIL",
            "info" if artifacts_ok else "error",
            "runtime_root",
            "required_outputs",
            "none_missing" if artifacts_ok else ";".join(sorted(missing_required_artifacts)),
        )
    )

    rows.extend(validation_rows)
    return rows


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
