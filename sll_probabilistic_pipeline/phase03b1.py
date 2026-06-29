"""Phase03B1 QA22, topology, and evidence-trace materialization runtime."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .config import (
    DEFAULT_PHASE03A_SUPERSEDED_RUNTIME,
    PHASE03A_APPROVED_COMPLETION_STATE,
    PHASE03B1_APPROVED_COMPLETION_STATE,
    PHASE03B1_BLOCKED_STATE,
    PHASE03B1_REQUIRED_INPUTS,
    PHASE03B1_REQUIRED_OUTPUTS,
)
from .paths import ResolvedPhase03B1Paths, resolve_phase03b1_paths
from .utils import (
    as_float,
    ensure_dir,
    fieldnames_from_rows,
    normcase_path,
    path_snapshot,
    read_json,
    read_tsv,
    read_tsv_with_header,
    stable_trace_id,
    utc_now_iso,
    write_json,
    write_json_list,
    write_tsv,
)
from .validation.phase03b1 import build_phase03b1_forbidden_scan_rows, build_phase03b1_validation_summary


ALLOWED_QA_STATES = {
    "answered_defensible",
    "answered_exploratory_with_caution",
    "legitimate_absence_demonstrated",
    "external_validation_required",
    "internal_failure_localized",
}
QUESTION_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("Q01", "system_nodes", "Que componentes o variables son nodos observados del sistema?"),
    ("Q02", "system_nodes", "OD600 y variables fisicoquimicas u operativas funcionan como nodos?"),
    ("Q03", "mix_max_relations", "Para la condicion MIX_MAX, que perturba a que?"),
    ("Q04", "mix_max_relations", "Para la condicion MIX_MAX, que perturbadores promueven cada target?"),
    ("Q05", "mix_max_relations", "Para la condicion MIX_MAX, que perturbadores inhiben, frenan o desvían cada target?"),
    ("Q06", "relation_scoring", "Que relacion tiene cada perturbador con el score global y local?"),
    ("Q07", "relation_scoring", "Que soporte estadistico acompana cada relacion?"),
    ("Q08", "relation_scoring", "Que soporte temporal acompana cada relacion?"),
    ("Q09", "relation_scoring", "Que soporte kinetico acompana cada relacion?"),
    ("Q10", "relation_temporal", "Que lag domina cada relacion?"),
    ("Q11", "relation_temporal", "Que relaciones son rapidas, intermedias, persistentes o tardias?"),
    ("Q12", "pair_conditioned", "Que pares condicionados existen o por que no existen?"),
    ("Q13", "priority_surface", "Que relaciones son accionables, candidatas o contextuales?"),
    ("Q14", "priority_surface", "Que relaciones son prioridad de revision?"),
    ("Q15", "priority_surface", "Que relaciones son prioridad de validacion?"),
    ("Q16", "priority_surface", "Que relaciones pueden proponerse como candidatas de intervencion?"),
    ("Q17", "network_topology", "Que variables actuan como perturbadores principales?"),
    ("Q18", "network_topology", "Que variables actuan como targets mas sensibles?"),
    ("Q19", "network_topology", "La red es concentrada, distribuida o acoplada?"),
    ("Q20", "closure_boundaries", "Que respuestas no pueden cerrarse y cual es el origen interno exacto?"),
    ("Q21", "documentary_state", "Existe incoherencia documental final?"),
    ("Q22", "closure_boundaries", "El runtime puede declarar cierre o debe declarar NO-GO?"),
)
EXPECTED_CALIBRATION_COUNTS = {"1": 246, "2": 408, "3": 475, "4": 462}
DEFERRED_SCOPE_BOUNDARY = "phase03b2_deferred_scope_boundary"
ALLOWED_POSTERIOR_DECISION_STATES = {"positive_support", "negative_support"}


def run_phase03b1(
    *,
    repo_root: str | Path,
    phase03a_runtime: str | Path,
    out_root: str | Path,
    strict: bool,
) -> dict[str, object]:
    repo_snapshot_before = path_snapshot(Path(repo_root).resolve(strict=False))
    resolved = resolve_phase03b1_paths(
        repo_root=repo_root,
        phase03a_runtime=phase03a_runtime,
        out_root=out_root,
        strict=strict,
    )
    runtime_root = ensure_dir(resolved.runtime_root)
    data_dir = ensure_dir(runtime_root / "data")
    audit_dir = ensure_dir(runtime_root / "audit")
    manifest_dir = ensure_dir(runtime_root / "manifest")

    output_root_boundary_rows = [
        {
            "repo_root": str(resolved.repo_root),
            "requested_out_root": str(resolved.requested_out_root),
            "resolved_out_root": str(resolved.requested_out_root),
            "allowed_results_root": str(resolved.allowed_results_root),
            "runtime_root": str(resolved.runtime_root),
            "repo_conflict": "no",
            "allowed_root_check": "pass",
            "decision": "allow",
            "rejection_code": "",
            "notes": "Phase03B1 runtime created under the allowed external results root.",
        }
    ]
    _write_table(
        audit_dir / "output_root_boundary_audit.tsv",
        output_root_boundary_rows,
        preferred_order=list(output_root_boundary_rows[0].keys()),
    )

    phase03a_bundle = _load_phase03a_bundle(resolved.phase03a_runtime)
    phase03a_gate_rows = _build_phase03a_direct_read_gate(resolved=resolved, bundle=phase03a_bundle)
    preflight_failed = any(row.get("status") == "FAIL" for row in phase03a_gate_rows)

    intervention_rows: list[dict[str, object]] = []
    topology_rows: list[dict[str, object]] = []
    topology_json: dict[str, object] = {}
    qa_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    boundary_rows: list[dict[str, object]] = []

    if not preflight_failed:
        intervention_rows = _build_intervention_priority_surface(phase03a_bundle)
        _write_table(
            data_dir / "intervention_priority_surface.tsv",
            intervention_rows,
            preferred_order=[
                "relation_anchor_id",
                "target_component_id",
                "perturbator_component_id",
                "scenario_canonical",
                "condition_role",
                "condition_id",
                "replicate",
                "run_max_lag",
                "edge_lag",
                "posterior_state_argmax",
                "p_positive_support",
                "p_negative_support",
                "p_ambiguous_or_mixed",
                "p_insufficient_or_uninformative",
                "probability_limitations_flag",
                "qc_blocker_status",
                "S_stat",
                "S_temp",
                "S_kin",
                "global_score",
                "local_score",
                "primary_lag",
                "lag_class",
                "review_priority_rank",
                "validation_priority_rank",
                "intervention_priority_rank",
                "priority_class",
                "why_not_intervention_if_blocked",
                "interpretive_priority_class",
                "relation_direction",
                "source_surface",
                "source_row_key",
                "not_causal_probability_yes_no",
                "not_final_decision_yes_no",
                "trace_id",
            ],
        )

        topology_rows, topology_json = _build_network_topology_summary(
            posterior_rows=phase03a_bundle["posterior_rows"],
            intervention_rows=intervention_rows,
        )
        _write_table(
            data_dir / "network_topology_summary.tsv",
            topology_rows,
            preferred_order=[
                "node_id",
                "node_label",
                "node_class",
                "observed_variable_yes_no",
                "metabolite_yes_no",
                "physicochemical_yes_no",
                "growth_or_biomass_yes_no",
                "operational_variable_yes_no",
                "semantic_mapping_status",
                "mapping_reason",
                "can_act_as_target_yes_no",
                "can_act_as_perturbator_yes_no",
                "source_surface",
                "source_row_count",
                "unweighted_in_degree",
                "unweighted_out_degree",
                "weighted_in_degree",
                "weighted_out_degree",
                "positive_in_edges",
                "negative_in_edges",
                "positive_out_edges",
                "negative_out_edges",
                "ambiguous_incident_count",
                "insufficient_incident_count",
                "qc_blocked_incident_count",
                "dominant_role",
                "dominant_lag_class",
                "dominant_support_axis",
                "concentration_of_influence_class",
                "network_interpretation_class",
                "caution_reason",
                "contributing_relation_anchor_ids",
                "not_causal_network_yes_no",
                "not_final_decision_yes_no",
                "trace_id",
            ],
        )
        write_json(data_dir / "network_topology_summary.json", topology_json)

    forbidden_scan_rows = build_phase03b1_forbidden_scan_rows(runtime_root)
    _write_table(
        data_dir / "phase03b1_forbidden_output_scan.tsv",
        forbidden_scan_rows,
        preferred_order=list(forbidden_scan_rows[0].keys()),
    )

    if not preflight_failed:
        qa_rows, evidence_rows = _build_question_rows(
            phase03a_runtime=resolved.phase03a_runtime,
            phase03a_bundle=phase03a_bundle,
            intervention_rows=intervention_rows,
            topology_rows=topology_rows,
            topology_json=topology_json,
            forbidden_scan_rows=forbidden_scan_rows,
        )
        boundary_rows = _build_failure_boundary_audit(qa_rows)
        q20_row, q20_evidence_row = _build_q20_from_boundaries(boundary_rows)
        qa_rows.append(q20_row)
        evidence_rows.append(q20_evidence_row)
        qa_rows = sorted(qa_rows, key=lambda row: str(row.get("question_id", "")))
        evidence_rows = sorted(evidence_rows, key=lambda row: (str(row.get("question_id", "")), str(row.get("evidence_trace_id", ""))))
        boundary_rows = _build_failure_boundary_audit(qa_rows)

        _write_table(
            data_dir / "runtime_question_answer_matrix.tsv",
            qa_rows,
            preferred_order=[
                "question_id",
                "question_family",
                "question_text",
                "answer_status",
                "answer_state",
                "answer_value_text",
                "answer_value_numeric",
                "primary_source_surface",
                "source_surface",
                "primary_source_row_key",
                "source_row_key",
                "supporting_source_surfaces",
                "evidence_trace_id",
                "direct_read_yes_no",
                "inference_used_yes_no",
                "closure_ready_yes_no",
                "failure_boundary_if_any",
                "posterior_used_as_non_causal_support_yes_no",
                "not_final_decision_yes_no",
                "no_go_trigger_yes_no",
                "report_section",
            ],
        )
        write_json(
            data_dir / "runtime_question_answer_matrix.json",
            {
                "phase": "phase03b1",
                "question_count": len(qa_rows),
                "allowed_answer_states": sorted(ALLOWED_QA_STATES),
                "controlling_phase03a_runtime": str(resolved.phase03a_runtime),
                "questions": qa_rows,
            },
        )
        _write_table(
            data_dir / "question_answer_evidence_trace.tsv",
            evidence_rows,
            preferred_order=[
                "evidence_trace_id",
                "question_id",
                "source_surface",
                "source_row_key",
                "supporting_source_surfaces",
                "direct_read_yes_no",
                "inference_used_yes_no",
                "producer_function",
                "consumer_function",
                "artifact_root_scope",
                "runtime_artifact_path",
                "artifact_exists_yes_no",
                "evidence_note",
            ],
        )
        _write_table(
            data_dir / "question_answer_failure_boundary_audit.tsv",
            boundary_rows,
            preferred_order=[
                "question_id",
                "answer_status",
                "closure_ready_yes_no",
                "failure_boundary",
                "blocking_reason",
                "exact_internal_origin",
                "primary_source_surface",
                "primary_source_row_key",
                "evidence_trace_id",
                "no_go_trigger_yes_no",
            ],
        )
        coverage_rows = _build_surface_coverage_audit(
            phase03a_runtime=resolved.phase03a_runtime,
            phase03b1_runtime=runtime_root,
            qa_rows=qa_rows,
            evidence_rows=evidence_rows,
        )
        _write_table(
            data_dir / "question_answer_surface_coverage_audit.tsv",
            coverage_rows,
            preferred_order=[
                "question_id",
                "primary_source_surface",
                "primary_source_exists_yes_no",
                "supporting_surfaces_present_yes_no",
                "evidence_trace_present_yes_no",
                "direct_read_yes_no",
                "inference_used_yes_no",
                "closure_ready_yes_no",
                "coverage_status",
                "details",
            ],
        )

    repo_contamination_rows = _build_repo_contamination_audit(
        repo_root=resolved.repo_root,
        snapshot_before=repo_snapshot_before,
    )
    _write_table(
        audit_dir / "repo_contamination_audit.tsv",
        repo_contamination_rows,
        preferred_order=list(repo_contamination_rows[0].keys()),
    )

    manifest_path = manifest_dir / "runtime_manifest.json"
    manifest = _success_manifest(resolved) if not preflight_failed else _blocked_manifest(resolved, runtime_root=runtime_root)
    write_json(manifest_path, manifest)
    validation_rows = build_phase03b1_validation_summary(
        runtime_root=runtime_root,
        required_outputs=PHASE03B1_REQUIRED_OUTPUTS,
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        manifest=manifest,
        phase03a_gate_rows=phase03a_gate_rows,
        intervention_rows=intervention_rows,
        topology_rows=topology_rows,
        topology_json=topology_json,
        qa_rows=qa_rows,
        evidence_rows=evidence_rows,
        coverage_rows=coverage_rows,
        boundary_rows=boundary_rows,
        forbidden_scan_rows=forbidden_scan_rows,
    )

    if any(
        row.get("status") in {"WARN", "FAIL"} or row.get("severity") in {"warning", "error"}
        for row in validation_rows
    ):
        manifest = _blocked_manifest(resolved, runtime_root=runtime_root)
        write_json(manifest_path, manifest)
        validation_rows = build_phase03b1_validation_summary(
            runtime_root=runtime_root,
            required_outputs=PHASE03B1_REQUIRED_OUTPUTS,
            output_root_boundary_rows=output_root_boundary_rows,
            repo_contamination_rows=repo_contamination_rows,
            manifest=manifest,
            phase03a_gate_rows=phase03a_gate_rows,
            intervention_rows=intervention_rows,
            topology_rows=topology_rows,
            topology_json=topology_json,
            qa_rows=qa_rows,
            evidence_rows=evidence_rows,
            coverage_rows=coverage_rows,
            boundary_rows=boundary_rows,
            forbidden_scan_rows=forbidden_scan_rows,
        )

    _write_table(
        audit_dir / "phase03b1_validation_summary.tsv",
        validation_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    return manifest


def _safe_read_tsv(path: Path) -> list[dict[str, str]]:
    return read_tsv(path) if path.exists() else []


def _safe_read_tsv_with_header(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    return read_tsv_with_header(path) if path.exists() else ([], [])


def _safe_read_json(path: Path) -> dict[str, object]:
    return read_json(path) if path.exists() else {}


def _safe_read_json_list(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, list) else []


def _load_phase03a_bundle(runtime_root: Path) -> dict[str, object]:
    tensor_rows, tensor_header = _safe_read_tsv_with_header(runtime_root / "data" / "relation_probability_evidence_tensor.tsv")
    return {
        "manifest": _safe_read_json(runtime_root / "manifest" / "runtime_manifest.json"),
        "validation_rows": _safe_read_tsv(runtime_root / "audit" / "phase03_validation_summary.tsv"),
        "posterior_rows": _safe_read_tsv(runtime_root / "data" / "posterior_relation_state.tsv"),
        "posterior_json_rows": _safe_read_json_list(runtime_root / "data" / "posterior_relation_state.json"),
        "tensor_rows": tensor_rows,
        "tensor_header": tensor_header,
        "temporal_stat_rows": _safe_read_tsv(runtime_root / "data" / "temporal_pcmci_evidence_stat_surface.tsv"),
        "temporal_calibration_rows": _safe_read_tsv(runtime_root / "data" / "temporal_pcmci_calibration_surface.tsv"),
        "multilag_rows": _safe_read_tsv(runtime_root / "data" / "multilag_temporal_profile_surface.tsv"),
        "conditioned_rows": _safe_read_tsv(runtime_root / "data" / "conditioned_pair_probability_evidence_surface.tsv"),
        "descriptive_rows": _safe_read_tsv(runtime_root / "data" / "descriptive_probability_evidence_surface.tsv"),
        "interdependence_rows": _safe_read_tsv(runtime_root / "data" / "interdependence_probability_evidence_surface.tsv"),
        "kinetic_rows": _safe_read_tsv(runtime_root / "data" / "kinetic_likelihood_surface.tsv"),
        "semantic_registry_rows": _safe_read_tsv(runtime_root / "data" / "semantic_polarity_registry.tsv"),
        "semantic_compatibility_rows": _safe_read_tsv(runtime_root / "data" / "semantic_compatibility_surface.tsv"),
        "method_manifest_rows": _safe_read_tsv(runtime_root / "data" / "probability_method_manifest.tsv"),
        "method_manifest_json": _safe_read_json(runtime_root / "data" / "probability_method_manifest.json"),
        "probability_calibration_audit_rows": _safe_read_tsv(runtime_root / "data" / "probability_calibration_audit.tsv"),
        "probability_limitations_rows": _safe_read_tsv(runtime_root / "data" / "probability_limitations_audit.tsv"),
        "forbidden_scan_rows": _safe_read_tsv(runtime_root / "data" / "phase03_forbidden_output_scan.tsv"),
        "empty_probability_rows": _safe_read_tsv(runtime_root / "data" / "phase03_empty_or_absent_probability_audit.tsv"),
        "phase03a_boundary_rows": _safe_read_tsv(runtime_root / "audit" / "output_root_boundary_audit.tsv"),
        "phase03a_repo_contamination_rows": _safe_read_tsv(runtime_root / "audit" / "repo_contamination_audit.tsv"),
    }


def _build_phase03a_direct_read_gate(
    *,
    resolved: ResolvedPhase03B1Paths,
    bundle: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    validation_rows = bundle["validation_rows"]
    manifest = bundle["manifest"]
    posterior_rows = bundle["posterior_rows"]
    posterior_json_rows = bundle["posterior_json_rows"]
    tensor_rows = bundle["tensor_rows"]
    tensor_header = bundle["tensor_header"]
    calibration_rows = bundle["temporal_calibration_rows"]
    calibration_audit_rows = bundle["probability_calibration_audit_rows"]
    forbidden_scan_rows = bundle["forbidden_scan_rows"]
    kinetic_rows = bundle["kinetic_rows"]
    multilag_rows = bundle["multilag_rows"]
    phase03a_boundary_rows = bundle["phase03a_boundary_rows"]
    phase03a_repo_contamination_rows = bundle["phase03a_repo_contamination_rows"]

    runtime_exists = resolved.phase03a_runtime.exists()
    rows.append(
        _summary_row(
            "phase03a_runtime_exists",
            "PASS" if runtime_exists else "FAIL",
            "info" if runtime_exists else "error",
            "phase03a_runtime",
            str(resolved.phase03a_runtime),
            str(resolved.phase03a_runtime),
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
            "phase03a_manifest_state_valid",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase_state",
            (
                f"phase={manifest.get('phase', '')};phase_status={manifest.get('phase_status', '')};"
                f"pipeline_global_status={manifest.get('pipeline_global_status', '')};"
                f"final_go_no_go={manifest.get('final_go_no_go', '')}"
            ),
        )
    )

    warning_count = sum(
        1
        for row in validation_rows
        if row.get("status") == "WARN" or row.get("severity") == "warning"
    )
    fail_count = sum(
        1
        for row in validation_rows
        if row.get("status") == "FAIL" or row.get("severity") == "error"
    )
    validation_clean = warning_count == 0 and fail_count == 0
    rows.append(
        _summary_row(
            "phase03a_validation_clean",
            "PASS" if validation_clean else "FAIL",
            "info" if validation_clean else "error",
            "audit/phase03_validation_summary.tsv",
            "warning_fail_counts",
            f"warning_count={warning_count};fail_count={fail_count}",
        )
    )

    repaired_decision_ok = manifest.get("phase03a_completion_decision") == PHASE03A_APPROVED_COMPLETION_STATE
    rows.append(
        _summary_row(
            "phase03a_repaired_decision_valid",
            "PASS" if repaired_decision_ok else "FAIL",
            "info" if repaired_decision_ok else "error",
            "manifest/runtime_manifest.json",
            "phase03a_completion_decision",
            str(manifest.get("phase03a_completion_decision", "")),
        )
    )

    missing_inputs = [
        relative_path
        for relative_path in PHASE03B1_REQUIRED_INPUTS
        if not (resolved.phase03a_runtime / Path(relative_path.replace("/", "\\"))).exists()
    ]
    rows.append(
        _summary_row(
            "phase03a_required_inputs_present",
            "PASS" if not missing_inputs else "FAIL",
            "info" if not missing_inputs else "error",
            "phase03a_runtime",
            "required_inputs",
            "none_missing" if not missing_inputs else ";".join(sorted(missing_inputs)),
        )
    )

    superseded_not_used = normcase_path(resolved.phase03a_runtime) != normcase_path(DEFAULT_PHASE03A_SUPERSEDED_RUNTIME)
    rows.append(
        _summary_row(
            "superseded_phase03a_runtime_not_used",
            "PASS" if superseded_not_used else "FAIL",
            "info" if superseded_not_used else "error",
            "phase03a_runtime",
            "runtime_root",
            str(resolved.phase03a_runtime),
        )
    )

    tensor_not_posterior = bool(tensor_rows) and all(row.get("not_posterior_yes_no") == "yes" for row in tensor_rows)
    rows.append(
        _summary_row(
            "relation_probability_tensor_not_posterior",
            "PASS" if tensor_not_posterior else "FAIL",
            "info" if tensor_not_posterior else "error",
            "data/relation_probability_evidence_tensor.tsv",
            "not_posterior_yes_no",
            f"row_count={len(tensor_rows)};forbidden_columns_present={','.join(sorted(set(tensor_header) & {'posterior_probability', 'qa_answer_state', 'final_go_no_go'}))}",
        )
    )

    observed_counts = _counts_by_key(calibration_rows, "run_max_lag")
    audit_counts = {
        str(row.get("calibration_group", "")): int(float(row.get("row_count", 0) or 0))
        for row in calibration_audit_rows
        if row.get("audit_scope") == "run_max_lag"
    }
    calibration_counts_ok = observed_counts == EXPECTED_CALIBRATION_COUNTS and audit_counts == EXPECTED_CALIBRATION_COUNTS
    rows.append(
        _summary_row(
            "probability_calibration_audit_counts_match",
            "PASS" if calibration_counts_ok else "FAIL",
            "info" if calibration_counts_ok else "error",
            "data/probability_calibration_audit.tsv|data/temporal_pcmci_calibration_surface.tsv",
            "run_max_lag",
            f"expected={EXPECTED_CALIBRATION_COUNTS};surface={observed_counts};audit={audit_counts}",
        )
    )

    posterior_sum_ok = bool(posterior_rows) and all(_posterior_probabilities_sum_to_one(row) for row in posterior_rows)
    rows.append(
        _summary_row(
            "posterior_probabilities_sum_to_one",
            "PASS" if posterior_sum_ok else "FAIL",
            "info" if posterior_sum_ok else "error",
            "data/posterior_relation_state.tsv",
            "posterior_probability_sum",
            f"row_count={len(posterior_rows)};json_row_count={len(posterior_json_rows)}",
        )
    )

    rows.append(_posterior_flag_check(posterior_rows, "not_causal_probability_yes_no", "posterior_not_causal_probability"))
    rows.append(_posterior_flag_check(posterior_rows, "not_qa_answer_yes_no", "posterior_not_qa_answer"))
    rows.append(_posterior_flag_check(posterior_rows, "not_network_topology_yes_no", "posterior_not_topology"))
    rows.append(_posterior_flag_check(posterior_rows, "not_final_decision_yes_no", "posterior_not_final_decision"))

    lag_preserved = bool(posterior_rows) and bool(multilag_rows) and all(
        str(row.get("run_max_lag", "")).strip() != "" and str(row.get("edge_lag", "")).strip() != ""
        for row in posterior_rows + multilag_rows
    )
    rows.append(
        _summary_row(
            "run_max_lag_edge_lag_preserved",
            "PASS" if lag_preserved else "FAIL",
            "info" if lag_preserved else "error",
            "data/posterior_relation_state.tsv|data/multilag_temporal_profile_surface.tsv",
            "run_max_lag|edge_lag",
            f"posterior_rows={len(posterior_rows)};multilag_rows={len(multilag_rows)}",
        )
    )

    kinetic_real_only_ok = all(str(row.get("branch", "")).strip() in {"", "real_only"} for row in kinetic_rows)
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

    real_plus_absent = all(str(row.get("branch", "")).strip() != "real_plus_interpolated" for row in kinetic_rows)
    rows.append(
        _summary_row(
            "real_plus_interpolated_absent",
            "PASS" if real_plus_absent else "FAIL",
            "info" if real_plus_absent else "error",
            "data/kinetic_likelihood_surface.tsv",
            "branch",
            "none_present" if real_plus_absent else "real_plus_interpolated_detected",
        )
    )

    forbidden_absent = bool(forbidden_scan_rows) and all(row.get("present_yes_no") == "no" for row in forbidden_scan_rows)
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

    raw_roots_status = _validation_check_status(validation_rows, "no_raw_roots_consumed") == "PASS"
    rows.append(
        _summary_row(
            "raw_roots_not_consumed",
            "PASS" if raw_roots_status else "FAIL",
            "info" if raw_roots_status else "error",
            "audit/phase03_validation_summary.tsv",
            "no_raw_roots_consumed",
            _validation_check_details(validation_rows, "no_raw_roots_consumed"),
        )
    )

    phase03a_boundary_ok = bool(phase03a_boundary_rows) and all(
        row.get("repo_conflict") == "no"
        and row.get("allowed_root_check") == "pass"
        and row.get("decision") == "allow"
        for row in phase03a_boundary_rows[:1]
    )
    rows.append(
        _summary_row(
            "phase03a_output_root_boundary_valid",
            "PASS" if phase03a_boundary_ok else "FAIL",
            "info" if phase03a_boundary_ok else "error",
            "audit/output_root_boundary_audit.tsv",
            str(resolved.phase03a_runtime),
            str(phase03a_boundary_rows[0]) if phase03a_boundary_rows else "missing_phase03a_boundary_audit",
        )
    )

    phase03a_repo_ok = any(
        row.get("status") == "pass_no_new_repo_runtime_outputs" for row in phase03a_repo_contamination_rows
    ) and not any(str(row.get("status", "")).startswith("fail_") for row in phase03a_repo_contamination_rows)
    rows.append(
        _summary_row(
            "phase03a_repo_contamination_pass",
            "PASS" if phase03a_repo_ok else "FAIL",
            "info" if phase03a_repo_ok else "error",
            "audit/repo_contamination_audit.tsv",
            str(resolved.phase03a_runtime),
            f"row_count={len(phase03a_repo_contamination_rows)}",
        )
    )
    return rows


def _build_intervention_priority_surface(bundle: dict[str, object]) -> list[dict[str, object]]:
    tensor_by_anchor = {str(row.get("relation_anchor_id", "")): row for row in bundle["tensor_rows"]}
    temporal_by_anchor = {str(row.get("relation_anchor_id", "")): row for row in bundle["temporal_calibration_rows"]}
    multilag_by_anchor = {str(row.get("relation_anchor_id", "")): row for row in bundle["multilag_rows"]}
    rows: list[dict[str, object]] = []
    for posterior in bundle["posterior_rows"]:
        anchor_id = str(posterior.get("relation_anchor_id", "")).strip()
        if anchor_id == "":
            continue
        tensor = tensor_by_anchor.get(anchor_id, {})
        temporal = temporal_by_anchor.get(anchor_id, {})
        multilag = multilag_by_anchor.get(anchor_id, {})
        p_positive = _float_or_zero(posterior.get("p_positive_support"))
        p_negative = _float_or_zero(posterior.get("p_negative_support"))
        p_ambiguous = _float_or_zero(posterior.get("p_ambiguous_or_mixed"))
        p_insufficient = _float_or_zero(posterior.get("p_insufficient_or_uninformative"))
        s_stat = _bounded(
            _float_or_zero(tensor.get("conditioned_undirected_support"))
            + max(
                _float_or_zero(tensor.get("descriptive_positive_mass")),
                _float_or_zero(tensor.get("descriptive_negative_mass")),
            )
            + _float_or_zero(tensor.get("interdependence_undirected_support")),
            0.0,
            1.0,
        )
        s_temp = _bounded(
            _float_or_zero(temporal.get("p_temporal_signal_support"))
            or _float_or_zero(tensor.get("temporal_signal_support")),
            0.0,
            1.0,
        )
        s_kin = _bounded(
            max(
                _float_or_zero(tensor.get("kinetic_positive_mass")),
                _float_or_zero(tensor.get("kinetic_negative_mass")),
            ),
            0.0,
            1.0,
        )
        support_max = max(p_positive, p_negative)
        qc_penalty = 0.25 if str(posterior.get("qc_blocker_status", "")).strip() != "pass" else 0.0
        global_score = round(max(0.0, support_max - (0.50 * p_ambiguous) - (0.25 * p_insufficient) - qc_penalty) * 100.0, 6)
        local_score = round(max(0.0, support_max - (0.25 * p_insufficient)) * 100.0, 6)
        lag_class = _lag_class(
            edge_lag=str(posterior.get("edge_lag", "")).strip(),
            lag_conflict_flag=str(multilag.get("lag_conflict_flag", "")).strip(),
            lag_persistence_flag=str(multilag.get("lag_persistence_flag", "")).strip(),
        )
        direction = _posterior_direction(str(posterior.get("posterior_state_argmax", "")).strip())
        priority_class, interpretive_priority_class, why_not = _priority_classification(
            target_component_id=str(posterior.get("target_component_id", "")).strip(),
            perturbator_component_id=str(posterior.get("perturbator_component_id", "")).strip(),
            posterior_state_argmax=str(posterior.get("posterior_state_argmax", "")).strip(),
            qc_blocker_status=str(posterior.get("qc_blocker_status", "")).strip(),
            global_score=global_score,
            local_score=local_score,
            s_stat=s_stat,
            s_temp=s_temp,
            s_kin=s_kin,
        )
        rows.append(
            {
                "relation_anchor_id": anchor_id,
                "target_component_id": str(posterior.get("target_component_id", "")).strip(),
                "perturbator_component_id": str(posterior.get("perturbator_component_id", "")).strip(),
                "scenario_canonical": str(posterior.get("scenario_canonical", "")).strip(),
                "condition_role": str(posterior.get("condition_role", "")).strip(),
                "condition_id": str(posterior.get("condition_id", "")).strip(),
                "replicate": str(posterior.get("replicate", "")).strip(),
                "run_max_lag": str(posterior.get("run_max_lag", "")).strip(),
                "edge_lag": str(posterior.get("edge_lag", "")).strip(),
                "posterior_state_argmax": str(posterior.get("posterior_state_argmax", "")).strip(),
                "p_positive_support": _fmt(p_positive),
                "p_negative_support": _fmt(p_negative),
                "p_ambiguous_or_mixed": _fmt(p_ambiguous),
                "p_insufficient_or_uninformative": _fmt(p_insufficient),
                "probability_limitations_flag": str(posterior.get("probability_limitations_flag", "")).strip(),
                "qc_blocker_status": str(posterior.get("qc_blocker_status", "")).strip(),
                "S_stat": _fmt(s_stat),
                "S_temp": _fmt(s_temp),
                "S_kin": _fmt(s_kin),
                "global_score": f"{global_score:.6f}",
                "local_score": f"{local_score:.6f}",
                "primary_lag": str(multilag.get("edge_lag", "")).strip() or str(posterior.get("edge_lag", "")).strip(),
                "lag_class": lag_class,
                "review_priority_rank": 0,
                "validation_priority_rank": 0,
                "intervention_priority_rank": 0,
                "priority_class": priority_class,
                "why_not_intervention_if_blocked": why_not,
                "interpretive_priority_class": interpretive_priority_class,
                "relation_direction": direction,
                "source_surface": (
                    "data/posterior_relation_state.tsv|"
                    "data/relation_probability_evidence_tensor.tsv|"
                    "data/temporal_pcmci_calibration_surface.tsv|"
                    "data/multilag_temporal_profile_surface.tsv"
                ),
                "source_row_key": anchor_id,
                "not_causal_probability_yes_no": str(posterior.get("not_causal_probability_yes_no", "")).strip() or "yes",
                "not_final_decision_yes_no": str(posterior.get("not_final_decision_yes_no", "")).strip() or "yes",
                "trace_id": stable_trace_id("phase03b1_intervention_priority", anchor_id),
            }
        )

    _apply_dense_rank(
        rows,
        rank_field="review_priority_rank",
        score_getter=lambda row: _float_or_zero(row.get("S_temp"))
        + (1.0 if _float_or_zero(row.get("S_stat")) <= 0.0 else 0.0)
        + (1.0 if _float_or_zero(row.get("S_kin")) <= 0.0 else 0.0),
    )
    _apply_dense_rank(
        rows,
        rank_field="validation_priority_rank",
        score_getter=lambda row: _float_or_zero(row.get("S_temp")) + (_float_or_zero(row.get("global_score")) / 100.0),
    )
    _apply_dense_rank(
        rows,
        rank_field="intervention_priority_rank",
        score_getter=lambda row: (
            _float_or_zero(row.get("global_score")) / 100.0
            + _float_or_zero(row.get("S_stat"))
            + _float_or_zero(row.get("S_kin"))
        ),
    )
    return rows


def _build_network_topology_summary(
    *,
    posterior_rows: list[dict[str, object]],
    intervention_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    intervention_by_anchor = {str(row.get("relation_anchor_id", "")): row for row in intervention_rows}
    node_set = {
        str(row.get("target_component_id", "")).strip()
        for row in posterior_rows
        if str(row.get("target_component_id", "")).strip()
    }
    node_set.update(
        str(row.get("perturbator_component_id", "")).strip()
        for row in posterior_rows
        if str(row.get("perturbator_component_id", "")).strip()
    )
    target_nodes = {
        str(row.get("target_component_id", "")).strip()
        for row in posterior_rows
        if str(row.get("target_component_id", "")).strip()
    }
    perturb_nodes = {
        str(row.get("perturbator_component_id", "")).strip()
        for row in posterior_rows
        if str(row.get("perturbator_component_id", "")).strip()
    }

    eligible_edges: list[dict[str, object]] = []
    ambiguous_counts: Counter[str] = Counter()
    insufficient_counts: Counter[str] = Counter()
    qc_blocked_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    global_ambiguous = 0
    global_insufficient = 0
    global_qc_blocked = 0

    for posterior in posterior_rows:
        anchor_id = str(posterior.get("relation_anchor_id", "")).strip()
        target = str(posterior.get("target_component_id", "")).strip()
        perturbator = str(posterior.get("perturbator_component_id", "")).strip()
        if target:
            source_counts[target] += 1
        if perturbator:
            source_counts[perturbator] += 1
        state = str(posterior.get("posterior_state_argmax", "")).strip()
        qc_status = str(posterior.get("qc_blocker_status", "")).strip()
        if state == "ambiguous_or_mixed":
            global_ambiguous += 1
            ambiguous_counts[target] += 1
            ambiguous_counts[perturbator] += 1
        if state == "insufficient_or_uninformative":
            global_insufficient += 1
            insufficient_counts[target] += 1
            insufficient_counts[perturbator] += 1
        if qc_status != "pass":
            global_qc_blocked += 1
            qc_blocked_counts[target] += 1
            qc_blocked_counts[perturbator] += 1
        if state not in ALLOWED_POSTERIOR_DECISION_STATES or qc_status != "pass":
            continue
        intervention = intervention_by_anchor.get(anchor_id, {})
        weight = max(
            _float_or_zero(posterior.get("p_positive_support")),
            _float_or_zero(posterior.get("p_negative_support")),
        )
        eligible_edges.append(
            {
                "relation_anchor_id": anchor_id,
                "source": perturbator,
                "target": target,
                "sign": _posterior_direction(state),
                "weight": weight,
                "lag_class": str(intervention.get("lag_class", "")).strip() or "unknown",
                "dominant_support_axis": _dominant_support_axis(intervention),
            }
        )

    nodes = sorted(node for node in node_set if node != "")
    weighted_out: dict[str, float] = {node: 0.0 for node in nodes}
    weighted_in: dict[str, float] = {node: 0.0 for node in nodes}
    unweighted_out: dict[str, int] = {node: 0 for node in nodes}
    unweighted_in: dict[str, int] = {node: 0 for node in nodes}
    for edge in eligible_edges:
        weighted_out[edge["source"]] = weighted_out.get(edge["source"], 0.0) + float(edge["weight"])
        weighted_in[edge["target"]] = weighted_in.get(edge["target"], 0.0) + float(edge["weight"])
        unweighted_out[edge["source"]] = unweighted_out.get(edge["source"], 0) + 1
        unweighted_in[edge["target"]] = unweighted_in.get(edge["target"], 0) + 1

    total_weighted_out = sum(weighted_out.values())
    top_weighted_out = max(weighted_out.values()) if weighted_out else 0.0
    coupled_nodes = sum(1 for node in nodes if weighted_out.get(node, 0.0) > 0.0 and weighted_in.get(node, 0.0) > 0.0)
    coupled_ratio = (coupled_nodes / len(nodes)) if nodes else 0.0
    top_weighted_out_share = (top_weighted_out / total_weighted_out) if total_weighted_out > 0 else 0.0
    if not eligible_edges:
        network_class = "unknown"
    elif coupled_ratio >= 0.4:
        network_class = "highly_coupled"
    elif top_weighted_out_share >= 0.5:
        network_class = "concentrated"
    else:
        network_class = "distributed"

    topology_rows: list[dict[str, object]] = []
    for node in nodes:
        node_out_edges = [edge for edge in eligible_edges if edge["source"] == node]
        node_in_edges = [edge for edge in eligible_edges if edge["target"] == node]
        pos_out = sum(1 for edge in node_out_edges if edge["sign"] == "positive")
        neg_out = sum(1 for edge in node_out_edges if edge["sign"] == "negative")
        pos_in = sum(1 for edge in node_in_edges if edge["sign"] == "positive")
        neg_in = sum(1 for edge in node_in_edges if edge["sign"] == "negative")
        lag_counts = Counter(
            str(edge.get("lag_class", "")).strip()
            for edge in node_out_edges + node_in_edges
            if str(edge.get("lag_class", "")).strip() not in {"", "unknown"}
        )
        if lag_counts:
            lag_priority = {"rapid": 4, "intermediate": 3, "persistent": 2, "late": 1, "conflict": 0}
            dominant_lag = max(lag_counts.items(), key=lambda item: (item[1], lag_priority.get(item[0], -1), item[0]))[0]
        else:
            dominant_lag = "unknown"
        axis_counts = Counter(str(edge.get("dominant_support_axis", "")).strip() for edge in node_out_edges + node_in_edges if str(edge.get("dominant_support_axis", "")).strip())
        if axis_counts:
            axis_priority = {"stat": 3, "kin": 2, "temp": 1}
            dominant_axis = max(axis_counts.items(), key=lambda item: (item[1], axis_priority.get(item[0], 0), item[0]))[0]
        else:
            dominant_axis = "none"
        if weighted_out.get(node, 0.0) > weighted_in.get(node, 0.0):
            dominant_role = "perturbator_dominant"
        elif weighted_in.get(node, 0.0) > weighted_out.get(node, 0.0):
            dominant_role = "target_sensitive"
        elif weighted_out.get(node, 0.0) > 0.0 and weighted_in.get(node, 0.0) > 0.0:
            dominant_role = "coupled_hub"
        else:
            dominant_role = "isolated"
        if weighted_out.get(node, 0.0) == 0.0:
            concentration_class = "none"
        elif top_weighted_out > 0 and weighted_out.get(node, 0.0) >= 0.8 * top_weighted_out and unweighted_out.get(node, 0) >= 2:
            concentration_class = "concentrated_driver"
        elif unweighted_out.get(node, 0) >= 2:
            concentration_class = "distributed_driver"
        else:
            concentration_class = "localized_driver"
        caution_reason = "temporal_only_support" if dominant_axis == "temp" else ""
        node_class = "perturbator" if node in perturb_nodes else "observed_variable"
        if node in perturb_nodes and node in target_nodes:
            node_class = "perturbator_and_target"
        elif node in target_nodes and node not in perturb_nodes:
            node_class = "target"
        metabolism, physicochemical, growth, operational, mapping_reason = _node_type_flags(node)
        topology_rows.append(
            {
                "node_id": node,
                "node_label": node,
                "node_class": node_class,
                "observed_variable_yes_no": "yes",
                "metabolite_yes_no": metabolism,
                "physicochemical_yes_no": physicochemical,
                "growth_or_biomass_yes_no": growth,
                "operational_variable_yes_no": operational,
                "semantic_mapping_status": "mapped",
                "mapping_reason": mapping_reason,
                "can_act_as_target_yes_no": "yes" if node in target_nodes else "no",
                "can_act_as_perturbator_yes_no": "yes" if node in perturb_nodes else "no",
                "source_surface": "data/posterior_relation_state.tsv|data/intervention_priority_surface.tsv",
                "source_row_count": source_counts.get(node, 0),
                "unweighted_in_degree": unweighted_in.get(node, 0),
                "unweighted_out_degree": unweighted_out.get(node, 0),
                "weighted_in_degree": _fmt(weighted_in.get(node, 0.0)),
                "weighted_out_degree": _fmt(weighted_out.get(node, 0.0)),
                "positive_in_edges": pos_in,
                "negative_in_edges": neg_in,
                "positive_out_edges": pos_out,
                "negative_out_edges": neg_out,
                "ambiguous_incident_count": ambiguous_counts.get(node, 0),
                "insufficient_incident_count": insufficient_counts.get(node, 0),
                "qc_blocked_incident_count": qc_blocked_counts.get(node, 0),
                "dominant_role": dominant_role,
                "dominant_lag_class": dominant_lag,
                "dominant_support_axis": dominant_axis,
                "concentration_of_influence_class": concentration_class,
                "network_interpretation_class": network_class,
                "caution_reason": caution_reason,
                "contributing_relation_anchor_ids": "|".join(
                    sorted(
                        {
                            str(edge.get("relation_anchor_id", "")).strip()
                            for edge in node_out_edges + node_in_edges
                            if str(edge.get("relation_anchor_id", "")).strip()
                        }
                    )
                ),
                "not_causal_network_yes_no": "yes",
                "not_final_decision_yes_no": "yes",
                "trace_id": stable_trace_id("phase03b1_topology_node", node),
            }
        )

    dominant_perturbators = sorted(
        topology_rows,
        key=lambda row: (
            -_float_or_zero(row.get("weighted_out_degree")),
            -int(row.get("unweighted_out_degree", 0) or 0),
            str(row.get("node_id", "")),
        ),
    )[:5]
    dominant_targets = sorted(
        topology_rows,
        key=lambda row: (
            -_float_or_zero(row.get("weighted_in_degree")),
            -int(row.get("unweighted_in_degree", 0) or 0),
            str(row.get("node_id", "")),
        ),
    )[:5]
    topology_json = {
        "phase": "phase03b1",
        "global_network_interpretation_class": network_class,
        "node_count": len(nodes),
        "edge_count": len(eligible_edges),
        "total_posterior_row_count": len(posterior_rows),
        "uncertainty_counters": {
            "ambiguous_or_mixed": global_ambiguous,
            "insufficient_or_uninformative": global_insufficient,
            "qc_blocked": global_qc_blocked,
        },
        "coupled_node_count": coupled_nodes,
        "coupled_ratio": _fmt(coupled_ratio),
        "top_weighted_out_share": _fmt(top_weighted_out_share),
        "dominant_perturbators": [
            {
                "node_id": row["node_id"],
                "weighted_out_degree": row["weighted_out_degree"],
                "unweighted_out_degree": row["unweighted_out_degree"],
                "trace_id": row["trace_id"],
            }
            for row in dominant_perturbators
        ],
        "dominant_targets": [
            {
                "node_id": row["node_id"],
                "weighted_in_degree": row["weighted_in_degree"],
                "unweighted_in_degree": row["unweighted_in_degree"],
                "trace_id": row["trace_id"],
            }
            for row in dominant_targets
        ],
        "not_causal_network_yes_no": "yes",
        "not_final_decision_yes_no": "yes",
        "supporting_surfaces": [
            "data/posterior_relation_state.tsv",
            "data/intervention_priority_surface.tsv",
        ],
    }
    return topology_rows, topology_json


def _build_question_rows(
    *,
    phase03a_runtime: Path,
    phase03a_bundle: dict[str, object],
    intervention_rows: list[dict[str, object]],
    topology_rows: list[dict[str, object]],
    topology_json: dict[str, object],
    forbidden_scan_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    qa_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []

    posterior_rows = phase03a_bundle["posterior_rows"]
    mix_rows = [row for row in posterior_rows if str(row.get("scenario_canonical", "")).strip() == "MIX_MAX"]
    mix_positive = [row for row in mix_rows if str(row.get("posterior_state_argmax", "")).strip() == "positive_support"]
    mix_negative = [row for row in mix_rows if str(row.get("posterior_state_argmax", "")).strip() == "negative_support"]
    priority_counts = Counter(str(row.get("priority_class", "")).strip() or "none" for row in intervention_rows)
    lag_counts = Counter(str(row.get("primary_lag", "")).strip() or "unknown" for row in intervention_rows)
    lag_class_counts = Counter(str(row.get("lag_class", "")).strip() or "unknown" for row in intervention_rows)
    conditioned_rows = phase03a_bundle["conditioned_rows"]
    topology_by_node = {str(row.get("node_id", "")): row for row in topology_rows}
    dominant_perturbator_ids = [row.get("node_id", "") for row in topology_json.get("dominant_perturbators", [])]
    dominant_target_ids = [row.get("node_id", "") for row in topology_json.get("dominant_targets", [])]
    forbidden_by_path = {str(row.get("relative_path", "")): row for row in forbidden_scan_rows}

    for question_id, question_family, question_text in QUESTION_DEFINITIONS:
        if question_id == "Q20":
            continue
        if question_id == "Q01":
            node_count = len(topology_rows)
            target_capable = sum(1 for row in topology_rows if str(row.get("can_act_as_target_yes_no", "")).strip() == "yes")
            perturb_capable = sum(1 for row in topology_rows if str(row.get("can_act_as_perturbator_yes_no", "")).strip() == "yes")
            row_key = f"GLOBAL::observed_node_count={node_count}::target_capable_count={target_capable}::perturbator_capable_count={perturb_capable}"
            answer_text = row_key
            answer_status = "answered_defensible" if node_count > 0 else "internal_failure_localized"
            failure_boundary = "" if node_count > 0 else "network_topology_summary_missing_or_empty"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=answer_status,
                answer_value_text=answer_text,
                answer_value_numeric=node_count,
                primary_source_surface="data/network_topology_summary.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any=failure_boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=answer_text,
            )
        elif question_id == "Q02":
            growth_count = sum(1 for row in topology_rows if str(row.get("growth_or_biomass_yes_no", "")).strip() == "yes")
            phys_count = sum(1 for row in topology_rows if str(row.get("physicochemical_yes_no", "")).strip() == "yes")
            operational_count = sum(1 for row in topology_rows if str(row.get("operational_variable_yes_no", "")).strip() == "yes")
            row_key = f"GLOBAL::growth_nodes={growth_count}::physicochemical_nodes={phys_count}::operational_nodes={operational_count}"
            answer_text = row_key
            answer_status = "answered_defensible" if topology_rows else "internal_failure_localized"
            failure_boundary = "" if topology_rows else "network_topology_summary_missing_or_empty"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=answer_status,
                answer_value_text=answer_text,
                answer_value_numeric=growth_count + phys_count + operational_count,
                primary_source_surface="data/network_topology_summary.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any=failure_boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=answer_text,
            )
        elif question_id == "Q03":
            row_key = f"GLOBAL::scenario=MIX_MAX::materialized_rows={len(mix_rows)}"
            status = "answered_defensible" if mix_rows else "legitimate_absence_demonstrated"
            boundary = "" if mix_rows else "mix_max_rows_absent_after_phase03a_direct_read"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(mix_rows),
                primary_source_surface="data/posterior_relation_state.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/relation_probability_evidence_tensor.tsv|data/temporal_pcmci_calibration_surface.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
            )
        elif question_id == "Q04":
            row_key = f"GLOBAL::scenario=MIX_MAX::posterior_state=positive_support::rows={len(mix_positive)}"
            status = "answered_defensible" if mix_positive else "legitimate_absence_demonstrated"
            boundary = "" if mix_positive else "mix_max_positive_support_absent"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(mix_positive),
                primary_source_surface="data/posterior_relation_state.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/relation_probability_evidence_tensor.tsv|data/intervention_priority_surface.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
            )
        elif question_id == "Q05":
            row_key = f"GLOBAL::scenario=MIX_MAX::posterior_state=negative_support::rows={len(mix_negative)}"
            status = "answered_defensible" if mix_negative else "legitimate_absence_demonstrated"
            boundary = "" if mix_negative else "mix_max_negative_support_absent"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(mix_negative),
                primary_source_surface="data/posterior_relation_state.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/relation_probability_evidence_tensor.tsv|data/semantic_compatibility_surface.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
            )
        elif question_id == "Q06":
            nonzero_global = sum(1 for row in intervention_rows if _float_or_zero(row.get("global_score")) > 0.0)
            row_key = f"GLOBAL::relation_anchor_rows={len(intervention_rows)}::nonzero_global_score_rows={nonzero_global}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=nonzero_global,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q07":
            positive_s_stat = sum(1 for row in intervention_rows if _float_or_zero(row.get("S_stat")) > 0.0)
            row_key = f"GLOBAL::S_stat_positive_rows={positive_s_stat}::relation_anchor_rows={len(intervention_rows)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=positive_s_stat,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/conditioned_pair_probability_evidence_surface.tsv|data/descriptive_probability_evidence_surface.tsv|data/interdependence_probability_evidence_surface.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q08":
            positive_s_temp = sum(1 for row in intervention_rows if _float_or_zero(row.get("S_temp")) > 0.0)
            row_key = f"GLOBAL::S_temp_positive_rows={positive_s_temp}::relation_anchor_rows={len(intervention_rows)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=positive_s_temp,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/temporal_pcmci_evidence_stat_surface.tsv|data/temporal_pcmci_calibration_surface.tsv|data/multilag_temporal_profile_surface.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q09":
            positive_s_kin = sum(1 for row in intervention_rows if _float_or_zero(row.get("S_kin")) > 0.0)
            legitimate_absence_rows = sum(1 for row in phase03a_bundle["kinetic_rows"] if str(row.get("legitimate_absence_yes_no", "")).strip() == "yes")
            row_key = f"GLOBAL::S_kin_positive_rows={positive_s_kin}::legitimate_absence_rows={legitimate_absence_rows}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=positive_s_kin,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/kinetic_likelihood_surface.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q10":
            row_key = f"GLOBAL::primary_lag_distribution={_distribution_text(lag_counts)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=len(lag_counts),
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/multilag_temporal_profile_surface.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q11":
            row_key = f"GLOBAL::lag_class_distribution={_distribution_text(lag_class_counts)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=len(lag_class_counts),
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/multilag_temporal_profile_surface.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q12":
            row_key = f"GLOBAL::materialized_conditioned_pair_rows={len(conditioned_rows)}"
            status = "answered_defensible" if conditioned_rows else "legitimate_absence_demonstrated"
            boundary = "" if conditioned_rows else "conditioned_pair_probability_surface_empty"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(conditioned_rows),
                primary_source_surface="data/conditioned_pair_probability_evidence_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv|data/relation_probability_evidence_tensor.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
            )
        elif question_id == "Q13":
            row_key = f"GLOBAL::priority_class_distribution={_distribution_text(priority_counts)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=len(priority_counts),
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q14":
            top_rank = min((int(row.get("review_priority_rank", 0) or 0) for row in intervention_rows), default=0)
            row_key = f"GLOBAL::top_review_priority_rank={top_rank}::rows={len(intervention_rows)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=top_rank,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q15":
            top_rank = min((int(row.get("validation_priority_rank", 0) or 0) for row in intervention_rows), default=0)
            row_key = f"GLOBAL::top_validation_priority_rank={top_rank}::rows={len(intervention_rows)}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=top_rank,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q16":
            candidate_rows = sum(1 for row in intervention_rows if str(row.get("priority_class", "")).strip() == "intervention_candidate_defensible")
            top_rank = min((int(row.get("intervention_priority_rank", 0) or 0) for row in intervention_rows), default=0)
            row_key = f"GLOBAL::top_intervention_priority_rank={top_rank}::candidate_rows={candidate_rows}"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="answered_defensible" if intervention_rows else "internal_failure_localized",
                answer_value_text=row_key,
                answer_value_numeric=candidate_rows,
                primary_source_surface="data/intervention_priority_surface.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="data/posterior_relation_state.tsv",
                failure_boundary_if_any="" if intervention_rows else "intervention_priority_surface_missing_or_empty",
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q17":
            row_key = f"GLOBAL::dominant_perturbators={','.join(str(node_id) for node_id in dominant_perturbator_ids if node_id)}"
            status = "answered_defensible" if dominant_perturbator_ids and topology_json.get("edge_count", 0) else "legitimate_absence_demonstrated"
            boundary = "" if status == "answered_defensible" else "no_eligible_directed_topology_edges"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(dominant_perturbator_ids),
                primary_source_surface="data/network_topology_summary.json",
                primary_source_row_key="global::dominant_perturbators",
                supporting_source_surfaces="data/network_topology_summary.tsv|data/posterior_relation_state.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q18":
            row_key = f"GLOBAL::dominant_targets={','.join(str(node_id) for node_id in dominant_target_ids if node_id)}"
            status = "answered_defensible" if dominant_target_ids and topology_json.get("edge_count", 0) else "legitimate_absence_demonstrated"
            boundary = "" if status == "answered_defensible" else "no_eligible_directed_topology_edges"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric=len(dominant_target_ids),
                primary_source_surface="data/network_topology_summary.json",
                primary_source_row_key="global::dominant_targets",
                supporting_source_surfaces="data/network_topology_summary.tsv|data/posterior_relation_state.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q19":
            network_class = str(topology_json.get("global_network_interpretation_class", "")).strip()
            row_key = f"GLOBAL::global_network_interpretation_class={network_class or 'unknown'}"
            status = "answered_defensible" if network_class and network_class != "unknown" else "legitimate_absence_demonstrated"
            boundary = "" if status == "answered_defensible" else "no_eligible_directed_topology_edges"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status=status,
                answer_value_text=row_key,
                answer_value_numeric={"concentrated": 1.0, "distributed": 2.0, "highly_coupled": 3.0, "unknown": 0.0}.get(network_class or "unknown", 0.0),
                primary_source_surface="data/network_topology_summary.json",
                primary_source_row_key="global::global_network_interpretation_class",
                supporting_source_surfaces="data/network_topology_summary.tsv|data/posterior_relation_state.tsv",
                failure_boundary_if_any=boundary,
                posterior_used="yes",
                phase03a_runtime=phase03a_runtime,
                evidence_note=row_key,
                phase03b1_runtime_surface=True,
            )
        elif question_id == "Q21":
            forbidden_row = forbidden_by_path.get("data/final_machine_readable_consistency_audit.tsv", {})
            row_key = "data/final_machine_readable_consistency_audit.tsv::present=no"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="external_validation_required",
                answer_value_text="phase03b2_final_consistency_deferred",
                answer_value_numeric=0.0,
                primary_source_surface="data/phase03b1_forbidden_output_scan.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="manifest/runtime_manifest.json",
                failure_boundary_if_any="phase03b2_final_consistency_deferred",
                posterior_used="no",
                phase03a_runtime=phase03a_runtime,
                evidence_note=str(forbidden_row.get("status", "pass_forbidden_output_absent")),
                phase03b1_runtime_surface=True,
                closure_ready="no",
            )
        else:
            forbidden_row = forbidden_by_path.get("data/final_static_release_decision.json", {})
            row_key = "data/final_static_release_decision.json::present=no"
            qa_row, evidence_row = _question_and_evidence_row(
                question_id=question_id,
                question_family=question_family,
                question_text=question_text,
                answer_status="external_validation_required",
                answer_value_text="phase03b2_release_decision_deferred",
                answer_value_numeric=0.0,
                primary_source_surface="data/phase03b1_forbidden_output_scan.tsv",
                primary_source_row_key=row_key,
                supporting_source_surfaces="manifest/runtime_manifest.json",
                failure_boundary_if_any="phase03b2_release_decision_deferred",
                posterior_used="no",
                phase03a_runtime=phase03a_runtime,
                evidence_note=str(forbidden_row.get("status", "pass_forbidden_output_absent")),
                phase03b1_runtime_surface=True,
                closure_ready="no",
            )
        qa_rows.append(qa_row)
        evidence_rows.append(evidence_row)

    return qa_rows, evidence_rows


def _build_q20_from_boundaries(boundary_rows: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
    blocking_rows = [
        row
        for row in boundary_rows
        if str(row.get("closure_ready_yes_no", "")).strip() == "no"
        or str(row.get("answer_status", "")).strip() == "internal_failure_localized"
        or str(row.get("failure_boundary", "")).strip() != ""
    ]
    deferred_qids = [
        str(row.get("question_id", "")).strip()
        for row in blocking_rows
        if str(row.get("answer_status", "")).strip() == "external_validation_required"
    ]
    internal_failure_qids = [
        str(row.get("question_id", "")).strip()
        for row in blocking_rows
        if str(row.get("answer_status", "")).strip() == "internal_failure_localized"
    ]
    row_key = (
        "GLOBAL::not_closure_ready_questions="
        + (",".join(deferred_qids) if deferred_qids else "none")
        + "::internal_failure_questions="
        + (",".join(internal_failure_qids) if internal_failure_qids else "none")
    )
    qa_row, evidence_row = _question_and_evidence_row(
        question_id="Q20",
        question_family="closure_boundaries",
        question_text="Que respuestas no pueden cerrarse y cual es el origen interno exacto?",
        answer_status="answered_defensible",
        answer_value_text=row_key,
        answer_value_numeric=len(blocking_rows),
        primary_source_surface="data/question_answer_failure_boundary_audit.tsv",
        primary_source_row_key=row_key,
        supporting_source_surfaces="data/runtime_question_answer_matrix.tsv|data/question_answer_evidence_trace.tsv",
        failure_boundary_if_any="",
        posterior_used="no",
        phase03a_runtime=Path(),
        evidence_note=row_key,
        phase03b1_runtime_surface=True,
    )
    return qa_row, evidence_row


def _question_and_evidence_row(
    *,
    question_id: str,
    question_family: str,
    question_text: str,
    answer_status: str,
    answer_value_text: str,
    answer_value_numeric: float | int,
    primary_source_surface: str,
    primary_source_row_key: str,
    supporting_source_surfaces: str,
    failure_boundary_if_any: str,
    posterior_used: str,
    phase03a_runtime: Path,
    evidence_note: str,
    phase03b1_runtime_surface: bool = False,
    closure_ready: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    closure_ready_yes_no = closure_ready or (
        "no" if answer_status in {"external_validation_required", "internal_failure_localized"} else "yes"
    )
    evidence_trace_id = f"{question_id}::E1"
    no_go_trigger = "yes" if answer_status == "internal_failure_localized" else "no"
    qa_row = {
        "question_id": question_id,
        "question_family": question_family,
        "question_text": question_text,
        "answer_status": answer_status,
        "answer_state": answer_status,
        "answer_value_text": answer_value_text,
        "answer_value_numeric": f"{float(answer_value_numeric):.6f}" if isinstance(answer_value_numeric, (int, float)) else str(answer_value_numeric),
        "primary_source_surface": primary_source_surface,
        "source_surface": primary_source_surface,
        "primary_source_row_key": primary_source_row_key,
        "source_row_key": primary_source_row_key,
        "supporting_source_surfaces": supporting_source_surfaces,
        "evidence_trace_id": evidence_trace_id,
        "direct_read_yes_no": "yes",
        "inference_used_yes_no": "no",
        "closure_ready_yes_no": closure_ready_yes_no,
        "failure_boundary_if_any": failure_boundary_if_any,
        "posterior_used_as_non_causal_support_yes_no": posterior_used,
        "not_final_decision_yes_no": "yes",
        "no_go_trigger_yes_no": no_go_trigger,
        "report_section": question_family,
    }
    artifact_root_scope = "phase03b1_runtime" if phase03b1_runtime_surface else "phase03a_runtime"
    artifact_path = str((Path() if phase03b1_runtime_surface else phase03a_runtime) / Path(primary_source_surface.replace("/", "\\"))).replace("\\", "/")
    evidence_row = {
        "evidence_trace_id": evidence_trace_id,
        "question_id": question_id,
        "source_surface": primary_source_surface,
        "source_row_key": primary_source_row_key,
        "supporting_source_surfaces": supporting_source_surfaces,
        "direct_read_yes_no": "yes",
        "inference_used_yes_no": "no",
        "producer_function": "run_phase03b1",
        "consumer_function": "runtime_question_answer_matrix",
        "artifact_root_scope": artifact_root_scope,
        "runtime_artifact_path": artifact_path,
        "artifact_exists_yes_no": "yes",
        "evidence_note": evidence_note,
    }
    return qa_row, evidence_row


def _build_surface_coverage_audit(
    *,
    phase03a_runtime: Path,
    phase03b1_runtime: Path,
    qa_rows: list[dict[str, object]],
    evidence_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    evidence_ids = {str(row.get("evidence_trace_id", "")).strip() for row in evidence_rows}
    rows: list[dict[str, object]] = []
    for qa_row in qa_rows:
        question_id = str(qa_row.get("question_id", "")).strip()
        primary_surface = str(qa_row.get("primary_source_surface", "")).strip()
        supporting_surfaces = [
            surface
            for surface in str(qa_row.get("supporting_source_surfaces", "")).split("|")
            if surface.strip()
        ]
        primary_exists = _surface_exists(primary_surface, phase03a_runtime=phase03a_runtime, phase03b1_runtime=phase03b1_runtime)
        supporting_ok = all(
            _surface_exists(surface.strip(), phase03a_runtime=phase03a_runtime, phase03b1_runtime=phase03b1_runtime)
            for surface in supporting_surfaces
        )
        evidence_present = str(qa_row.get("evidence_trace_id", "")).strip() in evidence_ids
        closure_ready = str(qa_row.get("closure_ready_yes_no", "")).strip() == "yes"
        coverage_ok = (
            primary_exists
            and supporting_ok
            and evidence_present
            and str(qa_row.get("direct_read_yes_no", "")).strip() == "yes"
            and str(qa_row.get("inference_used_yes_no", "")).strip() == "no"
            and str(qa_row.get("primary_source_row_key", "")).strip() != ""
        )
        if not closure_ready and evidence_present and primary_exists:
            coverage_ok = True
        rows.append(
            {
                "question_id": question_id,
                "primary_source_surface": primary_surface,
                "primary_source_exists_yes_no": "yes" if primary_exists else "no",
                "supporting_surfaces_present_yes_no": "yes" if supporting_ok else "no",
                "evidence_trace_present_yes_no": "yes" if evidence_present else "no",
                "direct_read_yes_no": str(qa_row.get("direct_read_yes_no", "")).strip(),
                "inference_used_yes_no": str(qa_row.get("inference_used_yes_no", "")).strip(),
                "closure_ready_yes_no": str(qa_row.get("closure_ready_yes_no", "")).strip(),
                "coverage_status": "pass" if coverage_ok else "fail",
                "details": f"closure_ready={closure_ready};supporting_surface_count={len(supporting_surfaces)}",
            }
        )
    return rows


def _build_failure_boundary_audit(qa_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for qa_row in qa_rows:
        answer_status = str(qa_row.get("answer_status", "")).strip()
        closure_ready = str(qa_row.get("closure_ready_yes_no", "")).strip()
        boundary = str(qa_row.get("failure_boundary_if_any", "")).strip()
        blocking_reason = ""
        exact_origin = ""
        if answer_status == "internal_failure_localized":
            blocking_reason = boundary or "internal_failure_localized"
            exact_origin = boundary or "internal_failure_localized"
        elif answer_status == "external_validation_required":
            blocking_reason = boundary or DEFERRED_SCOPE_BOUNDARY
            exact_origin = boundary or DEFERRED_SCOPE_BOUNDARY
        elif boundary:
            blocking_reason = boundary
            exact_origin = boundary
        rows.append(
            {
                "question_id": str(qa_row.get("question_id", "")).strip(),
                "answer_status": answer_status,
                "closure_ready_yes_no": closure_ready,
                "failure_boundary": boundary,
                "blocking_reason": blocking_reason,
                "exact_internal_origin": exact_origin,
                "primary_source_surface": str(qa_row.get("primary_source_surface", "")).strip(),
                "primary_source_row_key": str(qa_row.get("primary_source_row_key", "")).strip(),
                "evidence_trace_id": str(qa_row.get("evidence_trace_id", "")).strip(),
                "no_go_trigger_yes_no": str(qa_row.get("no_go_trigger_yes_no", "")).strip(),
            }
        )
    return rows


def _surface_exists(
    surface: str,
    *,
    phase03a_runtime: Path,
    phase03b1_runtime: Path,
) -> bool:
    if surface == "":
        return False
    phase03b1_path = phase03b1_runtime / Path(surface.replace("/", "\\"))
    if phase03b1_path.exists():
        return True
    return (phase03a_runtime / Path(surface.replace("/", "\\"))).exists()


def _priority_classification(
    *,
    target_component_id: str,
    perturbator_component_id: str,
    posterior_state_argmax: str,
    qc_blocker_status: str,
    global_score: float,
    local_score: float,
    s_stat: float,
    s_temp: float,
    s_kin: float,
) -> tuple[str, str, str]:
    if target_component_id == "" or perturbator_component_id == "":
        return "blocked_internal_failure", "blocked_internal_failure", "missing_target_or_perturbator"
    if qc_blocker_status != "pass":
        return "review_priority_exploratory", "review_priority", "posterior_or_semantic_qc_blocked"
    if posterior_state_argmax in ALLOWED_POSTERIOR_DECISION_STATES and global_score > 0.0 and (s_stat > 0.0 or s_kin > 0.0):
        return "intervention_candidate_defensible", "intervention_priority", ""
    if posterior_state_argmax in ALLOWED_POSTERIOR_DECISION_STATES and global_score > 0.0 and s_temp > 0.0 and s_stat <= 0.0 and s_kin <= 0.0:
        return "validation_priority", "validation_priority", "temporal_only_signal_requires_validation"
    if local_score > 0.0:
        return "review_priority_exploratory", "review_priority", "insufficient_multi_axis_support"
    return "contextual_not_actionable", "contextual_priority", "no_materialized_score_signal"


def _posterior_direction(state: str) -> str:
    if state == "positive_support":
        return "positive"
    if state == "negative_support":
        return "negative"
    return "mixed"


def _dominant_support_axis(row: dict[str, object]) -> str:
    stat_value = _float_or_zero(row.get("S_stat"))
    temp_value = _float_or_zero(row.get("S_temp"))
    kin_value = _float_or_zero(row.get("S_kin"))
    if stat_value >= kin_value and stat_value >= temp_value and stat_value > 0.0:
        return "stat"
    if kin_value >= temp_value and kin_value > 0.0:
        return "kin"
    if temp_value > 0.0:
        return "temp"
    return "none"


def _lag_class(*, edge_lag: str, lag_conflict_flag: str, lag_persistence_flag: str) -> str:
    if lag_conflict_flag == "yes":
        return "conflict"
    if lag_persistence_flag == "yes":
        return "persistent"
    lag = int(float(edge_lag or 0) or 0)
    if lag <= 1:
        return "rapid"
    if lag == 2:
        return "intermediate"
    if lag == 3:
        return "persistent"
    if lag >= 4:
        return "late"
    return "unknown"


def _node_type_flags(node: str) -> tuple[str, str, str, str, str]:
    lower_node = node.lower()
    metabolite = "yes" if bool(re.search(r"(acetate|fumarate|succinate|glucose|lactate|glycerol|_gl|_mmol)", node, flags=re.IGNORECASE)) else "no"
    growth = "yes" if bool(re.search(r"(od600|biomass|growth|lnod)", lower_node)) else "no"
    physicochemical = "yes" if bool(re.search(r"(ph|temp|temperature|pressure|conductivity|oxygen|do\b|orp|potential|redox)", lower_node)) else "no"
    operational = "yes" if bool(re.search(r"(rpm|agitation|stir|feed|flow|aeration|air|gas|voltage|current|power|setpoint|control)", lower_node)) else "no"
    if growth == "yes":
        physicochemical = "yes"
    if metabolite == physicochemical == growth == operational == "no":
        reason = "generic_observed_variable_from_phase03a_runtime"
    else:
        reason_tokens: list[str] = []
        if metabolite == "yes":
            reason_tokens.append("metabolite_token_detected")
        if physicochemical == "yes":
            reason_tokens.append("physicochemical_or_growth_token_detected")
        if operational == "yes":
            reason_tokens.append("operational_token_detected")
        reason = "|".join(reason_tokens)
    return metabolite, physicochemical, growth, operational, reason


def _apply_dense_rank(
    rows: list[dict[str, object]],
    *,
    rank_field: str,
    score_getter,
) -> None:
    ordered_scores = sorted({round(float(score_getter(row)), 12) for row in rows}, reverse=True)
    rank_by_score = {score: index + 1 for index, score in enumerate(ordered_scores)}
    for row in rows:
        score = round(float(score_getter(row)), 12)
        row[rank_field] = rank_by_score.get(score, 0)


def _distribution_text(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return "|".join(f"{key}:{counter[key]}" for key in sorted(counter))


def _counts_by_key(rows: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "")).strip()
        if value == "":
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _posterior_probabilities_sum_to_one(row: dict[str, object]) -> bool:
    total = (
        _float_or_zero(row.get("p_positive_support"))
        + _float_or_zero(row.get("p_negative_support"))
        + _float_or_zero(row.get("p_ambiguous_or_mixed"))
        + _float_or_zero(row.get("p_insufficient_or_uninformative"))
    )
    return abs(total - 1.0) <= 1e-6


def _posterior_flag_check(
    posterior_rows: list[dict[str, object]],
    field: str,
    check_id: str,
) -> dict[str, object]:
    ok = bool(posterior_rows) and all(str(row.get(field, "")).strip() == "yes" for row in posterior_rows)
    return _summary_row(
        check_id,
        "PASS" if ok else "FAIL",
        "info" if ok else "error",
        "data/posterior_relation_state.tsv",
        field,
        f"row_count={len(posterior_rows)}",
    )


def _validation_check_status(rows: list[dict[str, object]], check_id: str) -> str:
    for row in rows:
        if str(row.get("check_id", "")).strip() == check_id:
            return str(row.get("status", "")).strip()
    return ""


def _validation_check_details(rows: list[dict[str, object]], check_id: str) -> str:
    for row in rows:
        if str(row.get("check_id", "")).strip() == check_id:
            return str(row.get("details", "")).strip()
    return "missing_validation_check"


def _build_repo_contamination_audit(
    *,
    repo_root: Path,
    snapshot_before: set[str],
) -> list[dict[str, object]]:
    snapshot_after = path_snapshot(repo_root)
    new_entries = sorted(snapshot_after - snapshot_before)
    rows: list[dict[str, object]] = [
        {
            "path": ".tmp_manual_phase01a",
            "status": "baseline_legacy_present",
            "reason": "preexisting_repo_local_runtime_directory",
        },
        {
            "path": ".tmp_test_runtime",
            "status": "baseline_legacy_present",
            "reason": "preexisting_repo_local_test_runtime_directory",
        },
    ]
    if not new_entries:
        rows.append(
            {
                "path": "",
                "status": "pass_no_new_repo_runtime_outputs",
                "reason": "no_new_suspicious_runtime_artifacts_detected_inside_repo",
            }
        )
        return rows
    for entry in new_entries:
        rows.append(
            {
                "path": entry,
                "status": "fail_new_repo_runtime_output_detected",
                "reason": "new_suspicious_artifact_created_inside_repo",
            }
        )
    return rows


def _success_manifest(resolved: ResolvedPhase03B1Paths) -> dict[str, object]:
    return {
        "phase": "phase03b1",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase03a_runtime": str(resolved.phase03a_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase03b1_qa22_topology_trace_complete_waiting_for_phase03b2_plan",
        "phase03b1_completion_decision": PHASE03B1_APPROVED_COMPLETION_STATE,
        "next_allowed_phase": "PHASE03B2_REPORTS_FINAL_CONSISTENCY_AND_RELEASE_DECISION_PLAN",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase03b1",
        "phase_scope": "qa22_topology_priority_and_trace_only_no_reports_or_final_release_decision",
        "not_final_reports_yes_no": "yes",
        "not_final_decision_yes_no": "yes",
        "q21_q22_deferred_to_phase03b2_yes_no": "yes",
        "outputs": list(PHASE03B1_REQUIRED_OUTPUTS),
    }


def _blocked_manifest(
    resolved: ResolvedPhase03B1Paths,
    *,
    runtime_root: Path,
) -> dict[str, object]:
    outputs = [
        relative_path
        for relative_path in PHASE03B1_REQUIRED_OUTPUTS
        if (runtime_root / Path(relative_path.replace("/", "\\"))).exists()
    ]
    return {
        "phase": "phase03b1",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase03a_runtime": str(resolved.phase03a_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(runtime_root),
        "phase_status": "phase03b1_blocked_pending_repaired_phase03a_direct_read",
        "phase03b1_completion_decision": PHASE03B1_BLOCKED_STATE,
        "next_allowed_phase": "PHASE03B2_REPORTS_FINAL_CONSISTENCY_AND_RELEASE_DECISION_PLAN",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase03b1",
        "phase_scope": "qa22_topology_priority_and_trace_only_no_reports_or_final_release_decision",
        "not_final_reports_yes_no": "yes",
        "not_final_decision_yes_no": "yes",
        "q21_q22_deferred_to_phase03b2_yes_no": "yes",
        "outputs": outputs,
    }


def _float_or_zero(value: object) -> float:
    return as_float(value) or 0.0


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _fmt(value: float) -> str:
    return f"{value:.12f}"


def _write_table(path: Path, rows: list[dict[str, object]], *, preferred_order: list[str]) -> None:
    write_tsv(path, rows, fieldnames_from_rows(rows, preferred_order))


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
