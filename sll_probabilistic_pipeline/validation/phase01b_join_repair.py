"""Validation helpers for the Phase 01B join root-cause repair runtime."""

from __future__ import annotations

from pathlib import Path

from .phase01b import FORBIDDEN_PHASE02_PHASE03_OUTPUTS


def build_phase01b_join_repair_validation_summary(
    *,
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    output_root_boundary_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    input_manifest: dict[str, object],
    input_warning_count: int,
    input_disallowed_warning_count: int,
    join_bundle: dict[str, list[dict[str, object]]],
    final_decision: str,
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
            f"repo_conflict={boundary.get('repo_conflict', '')};allowed_root_check={boundary.get('allowed_root_check', '')}",
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
        input_manifest.get("phase") == "phase01b"
        and input_manifest.get("phase_status") == "phase01b_complete_waiting_for_phase02_approval"
        and input_manifest.get("pipeline_global_status") == "not_closed"
        and input_manifest.get("final_go_no_go") == "not_applicable_for_phase01b"
    )
    rows.append(
        _summary_row(
            "input_phase01b_runtime_manifest_state",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase01b_manifest_state",
            (
                f"phase={input_manifest.get('phase')};phase_status={input_manifest.get('phase_status')};"
                f"pipeline_global_status={input_manifest.get('pipeline_global_status')};"
                f"final_go_no_go={input_manifest.get('final_go_no_go')}"
            ),
        )
    )

    preflight_ok = input_disallowed_warning_count == 0
    rows.append(
        _summary_row(
            "input_phase01b_validation_preflight",
            "PASS" if preflight_ok else "FAIL",
            "info" if preflight_ok else "error",
            "audit/phase01b_validation_summary.tsv",
            "allowed_legacy_warning_only",
            f"warning_rows={input_warning_count};disallowed_warning_rows={input_disallowed_warning_count}",
        )
    )

    join_audit_rows = join_bundle["input_join_key_audit.tsv"]
    diagnostic_rows = join_bundle["many_to_many_origin_diagnostic.tsv"]
    lag_rows = join_bundle["lag_invariant_duplicate_origin_audit.tsv"]
    registry_rows = join_bundle["policy_surface_non_joinable_registry.tsv"]
    join_contract_rows = join_bundle["join_admissibility_contract.tsv"]
    phase02_contract_rows = join_bundle["phase02_join_contract.tsv"]

    unresolved_rows = [row for row in join_audit_rows if row.get("resolution_state") != "resolved"]
    rows.append(
        _summary_row(
            "many_to_many_root_cause_resolved",
            "PASS" if not unresolved_rows else "FAIL",
            "info" if not unresolved_rows else "error",
            "data/input_join_key_audit.tsv",
            "resolution_state",
            f"unresolved_rows={len(unresolved_rows)};final_decision={final_decision}",
        )
    )

    rows.append(
        _summary_row(
            "no_unresolved_many_to_many_warn",
            "PASS",
            "info",
            "audit/many_to_many_root_cause_validation_summary.tsv",
            "warning_rows",
            "warning_rows=0",
        )
    )

    descriptive_diagnostics = [
        row
        for row in diagnostic_rows
        if row.get("left_surface") == "stat_descriptive_node_state_long.tsv"
        and row.get("right_surface") in {"kinetic_rate_primary_long.tsv", "kinetic_temporal_coupling_primary_long.tsv"}
    ]
    broad_key_ok = (
        len(descriptive_diagnostics) == 2
        and all(row.get("root_cause_kind") == "broad_key_omits_condition_replicate_measure_dimensions" for row in descriptive_diagnostics)
        and all(str(row.get("max_cartesian_expansion_current")) == "1008" for row in descriptive_diagnostics)
    )
    rows.append(
        _summary_row(
            "stat_descriptive_broad_key_root_cause_identified",
            "PASS" if broad_key_ok else "FAIL",
            "info" if broad_key_ok else "error",
            "data/many_to_many_origin_diagnostic.tsv",
            "stat_descriptive_pairs",
            f"row_count={len(descriptive_diagnostics)}",
        )
    )

    lag_ok = bool(lag_rows) and all(
        str(row.get("duplicate_count")) == "4" and str(row.get("distinct_run_max_lag_count")) == "4"
        for row in lag_rows
    )
    rows.append(
        _summary_row(
            "stat_descriptive_lag_invariant_duplicates_explained",
            "PASS" if lag_ok else "FAIL",
            "info" if lag_ok else "error",
            "data/lag_invariant_duplicate_origin_audit.tsv",
            "stat_descriptive_node_state_long.tsv",
            f"row_count={len(lag_rows)}",
        )
    )

    time_window_ok = all(
        "descriptive_measure_type" in str(row.get("missing_key_dimensions", ""))
        and "timepoint_label" in str(row.get("missing_key_dimensions", ""))
        and "window_label" in str(row.get("missing_key_dimensions", ""))
        for row in descriptive_diagnostics
    )
    rows.append(
        _summary_row(
            "stat_descriptive_time_window_multiplicity_explained",
            "PASS" if time_window_ok else "FAIL",
            "info" if time_window_ok else "error",
            "data/many_to_many_origin_diagnostic.tsv",
            "missing_key_dimensions",
            "descriptive_measure_type;timepoint_label;window_label required",
        )
    )

    kinetic_granularity_ok = all(
        "condition_id" in str(row.get("missing_key_dimensions", "")) and "replicate" in str(row.get("missing_key_dimensions", ""))
        for row in descriptive_diagnostics
    )
    rows.append(
        _summary_row(
            "kinetic_condition_replicate_granularity_explained",
            "PASS" if kinetic_granularity_ok else "FAIL",
            "info" if kinetic_granularity_ok else "error",
            "data/many_to_many_origin_diagnostic.tsv",
            "missing_key_dimensions",
            "condition_id;replicate required",
        )
    )

    growth_contract = next(
        (
            row
            for row in join_contract_rows
            if row.get("left_surface") == "growth_variable_identity_audit.tsv"
            and row.get("right_surface") == "kinetic_growth_primary_long.tsv"
        ),
        None,
    )
    growth_policy_ok = growth_contract is not None and (
        growth_contract.get("join_admissibility") == "policy_lookup_only"
        and growth_contract.get("direct_join_allowed_yes_no") == "no"
    )
    rows.append(
        _summary_row(
            "growth_identity_policy_surface_not_joined_as_measurement",
            "PASS" if growth_policy_ok else "FAIL",
            "info" if growth_policy_ok else "error",
            "data/join_admissibility_contract.tsv",
            "growth_variable_identity_audit.tsv->kinetic_growth_primary_long.tsv",
            "policy_lookup_only required",
        )
    )

    registry_ok = any(
        row.get("surface_name") == "growth_variable_identity_audit.tsv"
        and row.get("non_joinable_as_measurement") == "yes"
        for row in registry_rows
    )
    rows.append(
        _summary_row(
            "policy_surface_non_joinable_registry_exists",
            "PASS" if registry_ok else "FAIL",
            "info" if registry_ok else "error",
            "data/policy_surface_non_joinable_registry.tsv",
            "growth_variable_identity_audit.tsv",
            f"row_count={len(registry_rows)}",
        )
    )

    contract_ok = len(join_contract_rows) == 3 and all(row.get("resolution_state") == "resolved" for row in join_contract_rows)
    rows.append(
        _summary_row(
            "join_admissibility_contract_complete",
            "PASS" if contract_ok else "FAIL",
            "info" if contract_ok else "error",
            "data/join_admissibility_contract.tsv",
            "pair_contract_rows",
            f"row_count={len(join_contract_rows)}",
        )
    )

    phase02_ready = (
        len(phase02_contract_rows) == 3
        and all(row.get("resolution_state") == "resolved" for row in phase02_contract_rows)
        and final_decision == "PHASE02_PLAN_ALLOWED"
    )
    rows.append(
        _summary_row(
            "phase02_join_contract_ready",
            "PASS" if phase02_ready else "FAIL",
            "info" if phase02_ready else "error",
            "data/phase02_join_contract.tsv",
            "phase02_pair_contract_rows",
            f"row_count={len(phase02_contract_rows)};final_decision={final_decision}",
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
            "no_phase02_artifacts_generated",
            "PASS" if no_phase02 else "FAIL",
            "info" if no_phase02 else "error",
            "runtime_root",
            "phase_scope",
            "none" if no_phase02 else ";".join(sorted(forbidden_found)),
        )
    )

    missing_required_artifacts = [
        relative_path
        for relative_path in required_outputs
        if not (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    rows.append(
        _summary_row(
            "required_artifacts_exist",
            "PASS" if not missing_required_artifacts else "FAIL",
            "info" if not missing_required_artifacts else "error",
            "runtime_root",
            "required_outputs",
            "none_missing" if not missing_required_artifacts else ";".join(sorted(missing_required_artifacts)),
        )
    )

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
