"""Validation helpers for Phase03B1 QA22, topology, and trace artifacts."""

from __future__ import annotations

from pathlib import Path

from ..config import PHASE03B1_APPROVED_COMPLETION_STATE, PHASE03B1_FORBIDDEN_OUTPUTS


ALLOWED_QA_STATES = {
    "answered_defensible",
    "answered_exploratory_with_caution",
    "legitimate_absence_demonstrated",
    "external_validation_required",
    "internal_failure_localized",
}
REQUIRED_QUESTION_IDS = {f"Q{index:02d}" for index in range(1, 23)}
DEFERRED_QUESTION_IDS = {"Q21", "Q22"}


def build_phase03b1_validation_summary(
    *,
    runtime_root: Path,
    required_outputs: tuple[str, ...],
    output_root_boundary_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    manifest: dict[str, object],
    phase03a_gate_rows: list[dict[str, object]],
    intervention_rows: list[dict[str, object]],
    topology_rows: list[dict[str, object]],
    topology_json: dict[str, object],
    qa_rows: list[dict[str, object]],
    evidence_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
    boundary_rows: list[dict[str, object]],
    forbidden_scan_rows: list[dict[str, object]],
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

    rows.extend(phase03a_gate_rows)

    qa_ids = {str(row.get("question_id", "")).strip() for row in qa_rows if str(row.get("question_id", "")).strip()}
    qa_all_present = qa_ids == REQUIRED_QUESTION_IDS
    rows.append(
        _summary_row(
            "qa22_all_questions_present",
            "PASS" if qa_all_present else "FAIL",
            "info" if qa_all_present else "error",
            "data/runtime_question_answer_matrix.tsv",
            "question_id",
            (
                "all_q01_q22_present"
                if qa_all_present
                else f"missing={sorted(REQUIRED_QUESTION_IDS - qa_ids)};extra={sorted(qa_ids - REQUIRED_QUESTION_IDS)}"
            ),
        )
    )

    allowed_states_ok = bool(qa_rows) and all(
        str(row.get("answer_status", "")).strip() in ALLOWED_QA_STATES
        and str(row.get("answer_state", "")).strip() in ALLOWED_QA_STATES
        for row in qa_rows
    )
    rows.append(
        _summary_row(
            "qa22_allowed_states_only",
            "PASS" if allowed_states_ok else "FAIL",
            "info" if allowed_states_ok else "error",
            "data/runtime_question_answer_matrix.tsv",
            "answer_status|answer_state",
            f"row_count={len(qa_rows)}",
        )
    )

    evidence_by_id = {
        str(row.get("evidence_trace_id", "")).strip(): row
        for row in evidence_rows
        if str(row.get("evidence_trace_id", "")).strip()
    }
    ad_rows = [row for row in qa_rows if str(row.get("answer_status", "")).strip() == "answered_defensible"]
    ad_trace_ok = all(
        str(row.get("direct_read_yes_no", "")).strip() == "yes"
        and str(row.get("inference_used_yes_no", "")).strip() == "no"
        and str(row.get("primary_source_surface", "")).strip() != ""
        and str(row.get("primary_source_row_key", "")).strip() != ""
        and str(row.get("evidence_trace_id", "")).strip() in evidence_by_id
        and str(evidence_by_id[str(row.get("evidence_trace_id", "")).strip()].get("direct_read_yes_no", "")).strip() == "yes"
        and str(evidence_by_id[str(row.get("evidence_trace_id", "")).strip()].get("inference_used_yes_no", "")).strip() == "no"
        for row in ad_rows
    )
    rows.append(
        _summary_row(
            "qa22_ad_rows_have_direct_trace",
            "PASS" if ad_trace_ok else "FAIL",
            "info" if ad_trace_ok else "error",
            "data/question_answer_evidence_trace.tsv",
            "answered_defensible",
            f"answered_defensible_rows={len(ad_rows)}",
        )
    )

    closure_rows = [
        row
        for row in qa_rows
        if str(row.get("closure_ready_yes_no", "")).strip() == "yes"
    ]
    no_narrative_only = all(
        str(row.get("direct_read_yes_no", "")).strip() == "yes"
        and str(row.get("inference_used_yes_no", "")).strip() == "no"
        and str(row.get("primary_source_surface", "")).strip() != ""
        and str(row.get("primary_source_row_key", "")).strip() != ""
        and str(row.get("evidence_trace_id", "")).strip() in evidence_by_id
        for row in closure_rows
    )
    rows.append(
        _summary_row(
            "qa22_no_narrative_only_closure",
            "PASS" if no_narrative_only else "FAIL",
            "info" if no_narrative_only else "error",
            "data/runtime_question_answer_matrix.tsv",
            "closure_ready_yes_no",
            f"closure_ready_rows={len(closure_rows)}",
        )
    )

    rows.append(
        _summary_row(
            "intervention_priority_surface_exists",
            "PASS" if bool(intervention_rows) else "FAIL",
            "info" if intervention_rows else "error",
            "data/intervention_priority_surface.tsv",
            "relation_anchor_id",
            f"row_count={len(intervention_rows)}",
        )
    )

    topology_exists = bool(topology_rows) and str(topology_json.get("global_network_interpretation_class", "")).strip() != ""
    rows.append(
        _summary_row(
            "topology_summary_exists",
            "PASS" if topology_exists else "FAIL",
            "info" if topology_exists else "error",
            "data/network_topology_summary.tsv|data/network_topology_summary.json",
            "global_network_interpretation_class",
            f"node_rows={len(topology_rows)}",
        )
    )

    topology_not_causal = bool(topology_rows) and all(
        str(row.get("not_causal_network_yes_no", "")).strip() == "yes" for row in topology_rows
    ) and str(topology_json.get("not_causal_network_yes_no", "")).strip() == "yes"
    rows.append(
        _summary_row(
            "topology_not_causal",
            "PASS" if topology_not_causal else "FAIL",
            "info" if topology_not_causal else "error",
            "data/network_topology_summary.tsv|data/network_topology_summary.json",
            "not_causal_network_yes_no",
            f"node_rows={len(topology_rows)}",
        )
    )

    qa_lookup = {str(row.get("question_id", "")).strip(): row for row in qa_rows}
    q21 = qa_lookup.get("Q21", {})
    q22 = qa_lookup.get("Q22", {})
    q21_q22_deferred = all(
        row
        and str(row.get("answer_status", "")).strip() in {
            "external_validation_required",
            "answered_exploratory_with_caution",
        }
        and str(row.get("closure_ready_yes_no", "")).strip() == "no"
        and str(row.get("not_final_decision_yes_no", "")).strip() == "yes"
        for row in (q21, q22)
    )
    rows.append(
        _summary_row(
            "q21_q22_final_decision_deferred",
            "PASS" if q21_q22_deferred else "FAIL",
            "info" if q21_q22_deferred else "error",
            "data/runtime_question_answer_matrix.tsv",
            "Q21|Q22",
            (
                f"Q21={q21.get('answer_status', '')}|{q21.get('closure_ready_yes_no', '')};"
                f"Q22={q22.get('answer_status', '')}|{q22.get('closure_ready_yes_no', '')}"
            ),
        )
    )

    forbidden_absent = all(row.get("present_yes_no") == "no" for row in forbidden_scan_rows)
    rows.append(
        _summary_row(
            "forbidden_outputs_absent",
            "PASS" if forbidden_absent else "FAIL",
            "info" if forbidden_absent else "error",
            "data/phase03b1_forbidden_output_scan.tsv",
            "forbidden_outputs",
            "none_present" if forbidden_absent else ";".join(
                str(row.get("relative_path", "")) for row in forbidden_scan_rows if row.get("present_yes_no") == "yes"
            ),
        )
    )

    deferred_outputs = {"audit/phase03b1_validation_summary.tsv"}
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

    status_complete = (
        manifest.get("phase") == "phase03b1"
        and manifest.get("phase_status") == "phase03b1_qa22_topology_trace_complete_waiting_for_phase03b2_plan"
        and manifest.get("phase03b1_completion_decision") == PHASE03B1_APPROVED_COMPLETION_STATE
        and manifest.get("final_go_no_go") == "not_applicable_for_phase03b1"
    )
    rows.append(
        _summary_row(
            "phase03b1_status_complete_waiting_for_phase03b2_plan",
            "PASS" if status_complete else "FAIL",
            "info" if status_complete else "error",
            "manifest/runtime_manifest.json",
            "phase03b1_completion_decision",
            (
                f"phase={manifest.get('phase', '')};phase_status={manifest.get('phase_status', '')};"
                f"phase03b1_completion_decision={manifest.get('phase03b1_completion_decision', '')};"
                f"final_go_no_go={manifest.get('final_go_no_go', '')}"
            ),
        )
    )

    coverage_exists = bool(coverage_rows)
    rows.append(
        _summary_row(
            "question_answer_surface_coverage_exists",
            "PASS" if coverage_exists else "FAIL",
            "info" if coverage_exists else "error",
            "data/question_answer_surface_coverage_audit.tsv",
            "question_id",
            f"row_count={len(coverage_rows)}",
        )
    )

    coverage_complete = bool(coverage_rows) and all(
        str(row.get("coverage_status", "")).strip() == "pass"
        for row in coverage_rows
    )
    rows.append(
        _summary_row(
            "question_answer_surface_coverage_complete",
            "PASS" if coverage_complete else "FAIL",
            "info" if coverage_complete else "error",
            "data/question_answer_surface_coverage_audit.tsv",
            "coverage_status",
            f"failures={sum(1 for row in coverage_rows if str(row.get('coverage_status', '')).strip() != 'pass')}",
        )
    )

    boundary_exists = bool(boundary_rows)
    rows.append(
        _summary_row(
            "question_answer_failure_boundary_exists",
            "PASS" if boundary_exists else "FAIL",
            "info" if boundary_exists else "error",
            "data/question_answer_failure_boundary_audit.tsv",
            "question_id",
            f"row_count={len(boundary_rows)}",
        )
    )

    return rows


def build_phase03b1_forbidden_scan_rows(runtime_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in PHASE03B1_FORBIDDEN_OUTPUTS:
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
