"""Validation helpers for Phase 02 relation evidence intake artifacts."""

from __future__ import annotations

from pathlib import Path

from ..config import PHASE02_APPROVED_COMPLETION_STATE, PHASE02_FORBIDDEN_OUTPUTS


FORBIDDEN_TENSOR_COLUMNS = {
    "posterior_probability",
    "P_signal",
    "P_state",
    "causal_probability",
    "final_score",
    "qa_answer_state",
    "network_degree",
    "final_go_no_go",
}


def build_phase02_validation_summary(
    *,
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    output_root_boundary_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    manifest: dict[str, object],
    preflight_rows: list[dict[str, object]],
    join_contract_audit_rows: list[dict[str, object]],
    anchor_rows: list[dict[str, object]],
    tensor_rows: list[dict[str, object]],
    tensor_fieldnames: list[str],
    forbidden_scan_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
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
        manifest.get("phase") == "phase02"
        and manifest.get("phase_status") == "phase02_relation_evidence_intake_complete_waiting_for_phase03_plan"
        and manifest.get("pipeline_global_status") == "not_closed"
        and manifest.get("final_go_no_go") == "not_applicable_for_phase02"
    )
    rows.append(
        _summary_row(
            "manifest_phase02_state",
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

    rows.append(_mirror_preflight(preflight_index, "phase01b_manifest_state_valid", "phase01b_runtime_manifest_valid"))
    rows.append(_mirror_preflight(preflight_index, "phase01b_validation_clean", "phase01b_validation_clean"))
    rows.append(_mirror_preflight(preflight_index, "phase01b_required_inputs_present", "phase02_required_inputs_present"))
    rows.append(_mirror_preflight(preflight_index, "no_raw_roots_consumed", "no_raw_roots_consumed"))

    join_contract_ok = bool(join_contract_audit_rows) and all(
        row.get("actual_consumption_status") == "pass" for row in join_contract_audit_rows
    )
    rows.append(
        _summary_row(
            "phase02_join_contract_consumed",
            "PASS" if join_contract_ok else "FAIL",
            "info" if join_contract_ok else "error",
            "data/phase02_join_contract_consumption_audit.tsv",
            "join_contract_rows",
            f"row_count={len(join_contract_audit_rows)}",
        )
    )

    join_admissibility_ok = bool(join_contract_audit_rows) and all(
        row.get("join_admissibility") in {"projection_only", "policy_lookup_only"}
        for row in join_contract_audit_rows
    )
    rows.append(
        _summary_row(
            "join_admissibility_contract_consumed",
            "PASS" if join_admissibility_ok else "FAIL",
            "info" if join_admissibility_ok else "error",
            "data/phase02_join_contract_consumption_audit.tsv",
            "join_admissibility",
            f"row_count={len(join_contract_audit_rows)}",
        )
    )

    kinetic_real_only_ok = all(row.get("branch", "") in {"", "real_only"} for row in kinetic_rows)
    rows.append(
        _summary_row(
            "kinetic_real_only_only",
            "PASS" if kinetic_real_only_ok else "FAIL",
            "info" if kinetic_real_only_ok else "error",
            "data/kinetic_*_evidence_intake.tsv",
            "branch",
            f"row_count={len(kinetic_rows)}",
        )
    )

    disabled_ok = all(row.get("branch") != "real_plus_interpolated" for row in kinetic_rows)
    rows.append(
        _summary_row(
            "real_plus_interpolated_disabled",
            "PASS" if disabled_ok else "FAIL",
            "info" if disabled_ok else "error",
            "data/kinetic_*_evidence_intake.tsv",
            "branch",
            f"row_count={len(kinetic_rows)}",
        )
    )

    lag_fields_present = bool(anchor_rows) and all(row.get("run_max_lag") != "" and row.get("edge_lag") != "" for row in anchor_rows)
    rows.append(
        _summary_row(
            "run_max_lag_edge_lag_preserved",
            "PASS" if lag_fields_present else "FAIL",
            "info" if lag_fields_present else "error",
            "data/relation_anchor_registry.tsv",
            "run_max_lag|edge_lag",
            f"row_count={len(anchor_rows)}",
        )
    )

    observed_lags = sorted({str(row.get("run_max_lag", "")) for row in anchor_rows if str(row.get("run_max_lag", ""))})
    no_global_priority_ok = len(observed_lags) > 1
    rows.append(
        _summary_row(
            "no_global_lag_priority",
            "PASS" if no_global_priority_ok else "FAIL",
            "info" if no_global_priority_ok else "error",
            "data/relation_anchor_registry.tsv",
            "run_max_lag",
            f"observed_run_max_lags={';'.join(observed_lags)}",
        )
    )

    anchors_exist = bool(anchor_rows)
    rows.append(
        _summary_row(
            "relation_anchor_registry_exists",
            "PASS" if anchors_exist else "FAIL",
            "info" if anchors_exist else "error",
            "data/relation_anchor_registry.tsv",
            "relation_anchor_rows",
            f"row_count={len(anchor_rows)}",
        )
    )

    tensor_exists = bool(tensor_rows)
    rows.append(
        _summary_row(
            "relation_evidence_tensor_exists",
            "PASS" if tensor_exists else "FAIL",
            "info" if tensor_exists else "error",
            "data/relation_evidence_tensor.tsv",
            "relation_tensor_rows",
            f"row_count={len(tensor_rows)}",
        )
    )

    tensor_ok = (
        not (FORBIDDEN_TENSOR_COLUMNS & set(tensor_fieldnames))
        and all(row.get("not_posterior_yes_no") == "yes" for row in tensor_rows)
    )
    rows.append(
        _summary_row(
            "relation_evidence_tensor_not_posterior",
            "PASS" if tensor_ok else "FAIL",
            "info" if tensor_ok else "error",
            "data/relation_evidence_tensor.tsv",
            "tensor_fields",
            ";".join(sorted(FORBIDDEN_TENSOR_COLUMNS & set(tensor_fieldnames))) or "not_posterior_yes_no=yes",
        )
    )

    forbidden_absent = all(row.get("present_yes_no") == "no" for row in forbidden_scan_rows)
    rows.append(
        _summary_row(
            "forbidden_outputs_absent",
            "PASS" if forbidden_absent else "FAIL",
            "info" if forbidden_absent else "error",
            "data/phase02_forbidden_output_scan.tsv",
            "forbidden_outputs",
            "none_present" if forbidden_absent else ";".join(
                str(row.get("relative_path", "")) for row in forbidden_scan_rows if row.get("present_yes_no") == "yes"
            ),
        )
    )

    deferred_outputs = {"audit/phase02_validation_summary.tsv"}
    missing_required = [
        relative_path
        for relative_path in required_outputs
        if relative_path not in deferred_outputs
        and not (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    required_ok = not missing_required
    rows.append(
        _summary_row(
            "required_artifacts_exist",
            "PASS" if required_ok else "FAIL",
            "info" if required_ok else "error",
            "runtime_root",
            "required_outputs",
            "none_missing" if required_ok else ";".join(sorted(missing_required)),
        )
    )

    empty_audit_ok = bool(empty_or_absent_rows)
    rows.append(
        _summary_row(
            "phase02_empty_or_absent_evidence_audit_exists",
            "PASS" if empty_audit_ok else "FAIL",
            "info" if empty_audit_ok else "error",
            "data/phase02_empty_or_absent_evidence_audit.tsv",
            "evidence_audit_rows",
            f"row_count={len(empty_or_absent_rows)}",
        )
    )

    status_complete = manifest.get("phase02_completion_decision") == PHASE02_APPROVED_COMPLETION_STATE
    rows.append(
        _summary_row(
            "phase02_status_complete_waiting_for_phase03_plan",
            "PASS" if status_complete else "FAIL",
            "info" if status_complete else "error",
            "manifest/runtime_manifest.json",
            "phase02_completion_decision",
            str(manifest.get("phase02_completion_decision", "")),
        )
    )

    rows.extend(preflight_rows)
    return rows


def build_phase02_forbidden_scan_rows(runtime_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in PHASE02_FORBIDDEN_OUTPUTS:
        present = (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
        rows.append(
            {
                "relative_path": relative_path,
                "present_yes_no": "yes" if present else "no",
                "status": "fail_forbidden_output_present" if present else "pass_forbidden_output_absent",
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
