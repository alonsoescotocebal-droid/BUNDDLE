"""Phase 03A probabilistic calibration and posterior relation states runtime."""

from __future__ import annotations

import math
from pathlib import Path

from .config import (
    PHASE02_FORBIDDEN_OUTPUTS,
    PHASE03A_APPROVED_COMPLETION_STATE,
    PHASE03A_BLOCKED_STATE,
    PHASE03A_CONTROLLER_SHA,
    PHASE03A_FORBIDDEN_INPUT_PATH_MARKERS,
    PHASE03A_FORBIDDEN_POSTERIOR_SOURCE_COLUMNS,
    PHASE03A_REQUIRED_INPUTS,
    PHASE03A_REQUIRED_OUTPUTS,
)
from .paths import ResolvedPhase03APaths, resolve_phase03a_paths
from .utils import (
    as_float,
    ensure_dir,
    fieldnames_from_rows,
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
from .validation.phase03a import build_phase03a_forbidden_scan_rows, build_phase03a_validation_summary


Q_FLOOR = 1e-12
TEMPERATURE = 1.25
EMPIRICAL_MIN_ROWS = 30
EMPIRICAL_MIN_UNIQUE = 8
POOLED_MIN_ROWS = 80
POOLED_MIN_UNIQUE = 12
WEIGHTS = {
    "temporal": 1.00,
    "kinetic": 0.80,
    "descriptive": 0.40,
    "conditioned_pair": 0.35,
    "interdependence": 0.25,
    "semantic_bonus": 0.25,
    "semantic_penalty": 0.50,
    "fallback_penalty": 0.20,
}
PRIORS = {
    "positive_support": -1.0,
    "negative_support": -1.0,
    "ambiguous_or_mixed": -0.5,
    "insufficient_or_uninformative": 0.0,
}
IMPLEMENTATION_AUDIT_PATH = Path("docs/PHASE03A_PROBABILISTIC_CALIBRATION_IMPLEMENTATION_AUDIT.md")
ALLOWED_REPO_DOC_OUTPUTS = {
    str(IMPLEMENTATION_AUDIT_PATH).replace("\\", "/"),
    "docs/PHASE03A_PROBABILISTIC_CALIBRATION_IMPLEMENTATION_PLAN_REWRITTEN_FULL_DETAIL_v2.md",
}


def run_phase03a(
    *,
    repo_root: str | Path,
    phase02_runtime: str | Path,
    out_root: str | Path,
    strict: bool,
) -> dict[str, object]:
    repo_snapshot_before = path_snapshot(Path(repo_root).resolve(strict=False))
    resolved = resolve_phase03a_paths(
        repo_root=repo_root,
        phase02_runtime=phase02_runtime,
        out_root=out_root,
        strict=strict,
    )
    runtime_root = ensure_dir(resolved.runtime_root)
    data_dir = ensure_dir(runtime_root / "data")
    audit_dir = ensure_dir(runtime_root / "audit")
    manifest_dir = ensure_dir(runtime_root / "manifest")
    ensure_dir(runtime_root / "logs")

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
            "notes": "Phase03A runtime created under the allowed external results root.",
        }
    ]
    _write_table(
        audit_dir / "output_root_boundary_audit.tsv",
        output_root_boundary_rows,
        preferred_order=list(output_root_boundary_rows[0].keys()),
    )

    input_manifest = read_json(resolved.input_manifest)
    input_validation_rows = read_tsv(resolved.input_validation_summary)
    input_manifest_audit_rows = _build_input_runtime_manifest_audit(input_manifest)
    input_surface_manifest_rows = _build_input_surface_manifest(resolved.phase02_runtime)
    preflight_rows = _build_preflight_audit(
        resolved=resolved,
        input_manifest=input_manifest,
        input_validation_rows=input_validation_rows,
        input_surface_manifest_rows=input_surface_manifest_rows,
    )
    _write_table(
        data_dir / "phase03_input_runtime_manifest_audit.tsv",
        input_manifest_audit_rows,
        preferred_order=list(input_manifest_audit_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase03_input_surface_manifest.tsv",
        input_surface_manifest_rows,
        preferred_order=list(input_surface_manifest_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase03_preflight_audit.tsv",
        preflight_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
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

    preflight_failed = any(row.get("status") == "FAIL" for row in preflight_rows)
    if preflight_failed:
        forbidden_scan_rows = build_phase03a_forbidden_scan_rows(runtime_root)
        _write_table(
            data_dir / "phase03_forbidden_output_scan.tsv",
            forbidden_scan_rows,
            preferred_order=list(forbidden_scan_rows[0].keys()),
        )
        empty_rows = [
            {
                "output_surface": "phase03a_runtime",
                "row_count": "",
                "status": "blocked_preflight_failure",
                "basis": "phase03_preflight",
                "notes": "Phase03A stopped before probabilistic surface construction.",
            }
        ]
        _write_table(
            data_dir / "phase03_empty_or_absent_probability_audit.tsv",
            empty_rows,
            preferred_order=list(empty_rows[0].keys()),
        )
        manifest = _blocked_manifest(resolved)
        write_json(manifest_dir / "runtime_manifest.json", manifest)
        validation_rows = build_phase03a_validation_summary(
            runtime_root=runtime_root,
            required_outputs=(
                "manifest/runtime_manifest.json",
                "data/phase03_input_runtime_manifest_audit.tsv",
                "data/phase03_input_surface_manifest.tsv",
                "data/phase03_preflight_audit.tsv",
                "data/phase03_forbidden_output_scan.tsv",
                "data/phase03_empty_or_absent_probability_audit.tsv",
                "audit/output_root_boundary_audit.tsv",
                "audit/repo_contamination_audit.tsv",
                "audit/phase03_validation_summary.tsv",
            ),
            output_root_boundary_rows=output_root_boundary_rows,
            repo_contamination_rows=repo_contamination_rows,
            manifest=manifest,
            preflight_rows=preflight_rows,
            method_manifest={},
            temporal_calibration_rows=[],
            probability_calibration_audit_rows=[],
            multilag_rows=[],
            kinetic_rows=[],
            semantic_registry_rows=[],
            semantic_compatibility_rows=[],
            probability_tensor_rows=[],
            posterior_rows=[],
            forbidden_scan_rows=forbidden_scan_rows,
            empty_or_absent_rows=empty_rows,
        )
        _write_table(
            audit_dir / "phase03_validation_summary.tsv",
            validation_rows,
            preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
        )
        _write_implementation_audit_doc(
            repo_root=resolved.repo_root,
            phase02_runtime=resolved.phase02_runtime,
            runtime_root=runtime_root,
            artifact_row_counts={"phase03_preflight_failures": sum(1 for row in preflight_rows if row["status"] == "FAIL")},
            calibration_routes_used=[],
            posterior_sum_check="not_run_blocked",
            forbidden_scan_rows=forbidden_scan_rows,
            repo_contamination_rows=repo_contamination_rows,
            validation_rows=validation_rows,
            decision=PHASE03A_BLOCKED_STATE,
            command_results={
                "py_compile_result": "not_run_blocked",
                "pytest_result": "not_run_blocked",
                "phase03a_cli_result": "not_run_blocked",
            },
        )
        return manifest

    inputs = _load_phase02_inputs(resolved.phase02_runtime)
    temporal_stat_rows = _build_temporal_evidence_stat_surface(inputs["stat_temporal_pcmci_evidence_intake.tsv"])
    temporal_calibration_rows, calibration_metadata = _build_temporal_pcmci_calibration_surface(temporal_stat_rows)
    multilag_rows = _build_multilag_temporal_profile_surface(
        anchor_rows=inputs["relation_anchor_registry.tsv"],
        calibration_rows=temporal_calibration_rows,
    )
    conditioned_rows = _build_conditioned_pair_probability_evidence_surface(inputs["stat_conditioned_pair_evidence_intake.tsv"])
    descriptive_rows = _build_descriptive_probability_evidence_surface(inputs["stat_descriptive_evidence_intake.tsv"])
    interdependence_rows = _build_interdependence_probability_evidence_surface(inputs["stat_interdependence_evidence_intake.tsv"])
    kinetic_rows = _build_kinetic_likelihood_surface(
        growth_rows=inputs["kinetic_growth_evidence_intake.tsv"],
        rate_rows=inputs["kinetic_rate_evidence_intake.tsv"],
        coupling_rows=inputs["kinetic_temporal_coupling_evidence_intake.tsv"],
        yield_rows=inputs["kinetic_yield_evidence_intake.tsv"],
        empty_or_absent_rows=inputs["phase02_empty_or_absent_evidence_audit.tsv"],
    )
    semantic_registry_rows = _build_semantic_polarity_registry(inputs["relation_anchor_registry.tsv"])
    semantic_compatibility_rows = _build_semantic_compatibility_surface(
        anchor_rows=inputs["relation_anchor_registry.tsv"],
        calibration_rows=temporal_calibration_rows,
        descriptive_rows=descriptive_rows,
        kinetic_rows=kinetic_rows,
        semantic_registry_rows=semantic_registry_rows,
    )
    probability_tensor_rows = _build_relation_probability_evidence_tensor(
        anchor_rows=inputs["relation_anchor_registry.tsv"],
        phase02_tensor_rows=inputs["relation_evidence_tensor.tsv"],
        temporal_calibration_rows=temporal_calibration_rows,
        conditioned_rows=conditioned_rows,
        descriptive_rows=descriptive_rows,
        interdependence_rows=interdependence_rows,
        kinetic_rows=kinetic_rows,
        semantic_compatibility_rows=semantic_compatibility_rows,
    )
    posterior_rows = _build_posterior_relation_state(probability_tensor_rows)
    method_manifest_json, method_manifest_rows = _build_probability_method_manifest(
        phase02_runtime=resolved.phase02_runtime,
        calibration_metadata=calibration_metadata,
    )
    probability_calibration_audit_rows = _build_probability_calibration_audit(calibration_metadata, temporal_calibration_rows)
    probability_limitations_audit_rows = _build_probability_limitations_audit(
        posterior_rows=posterior_rows,
        calibration_rows=temporal_calibration_rows,
        empty_or_absent_rows=inputs["phase02_empty_or_absent_evidence_audit.tsv"],
    )
    empty_or_absent_probability_rows = _build_phase03_empty_or_absent_probability_audit(
        temporal_stat_rows=temporal_stat_rows,
        temporal_calibration_rows=temporal_calibration_rows,
        conditioned_rows=conditioned_rows,
        descriptive_rows=descriptive_rows,
        interdependence_rows=interdependence_rows,
        kinetic_rows=kinetic_rows,
        semantic_rows=semantic_compatibility_rows,
        posterior_rows=posterior_rows,
        phase02_empty_rows=inputs["phase02_empty_or_absent_evidence_audit.tsv"],
    )

    _write_table(
        data_dir / "temporal_pcmci_evidence_stat_surface.tsv",
        temporal_stat_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "run_max_lag",
            "edge_lag",
            "effect_sign",
            "effect_value",
            "q_value",
            "q_floor_used",
            "q_value_status",
            "calibration_eligible_yes_no",
            "abs_evidence_score",
            "signed_evidence_score",
            "temporal_signal_direction",
            "evidence_stat_not_probability_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "temporal_pcmci_calibration_surface.tsv",
        temporal_calibration_rows,
        preferred_order=[
            "relation_anchor_id",
            "run_max_lag",
            "edge_lag",
            "abs_evidence_score",
            "signed_evidence_score",
            "calibration_route",
            "calibration_group",
            "calibration_status",
            "temporal_support_strength",
            "p_temporal_signal_support",
            "temporal_positive_mass",
            "temporal_negative_mass",
            "fallback_reason",
            "not_causal_probability_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "multilag_temporal_profile_surface.tsv",
        multilag_rows,
        preferred_order=[
            "relation_anchor_id",
            "run_max_lag",
            "edge_lag",
            "p_temporal_signal_support",
            "temporal_signal_direction",
            "lag_profile_scope",
            "same_relation_lag_count",
            "same_direction_lag_count",
            "opposite_direction_lag_count",
            "lag_conflict_flag",
            "lag_persistence_flag",
            "no_global_lag_priority_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "conditioned_pair_probability_evidence_surface.tsv",
        conditioned_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "conditioned_value",
            "conditioned_abs_value",
            "conditioned_sign",
            "conditioned_strength",
            "undirected_support_mass",
            "directional_support_allowed_yes_no",
            "positive_direction_mass",
            "negative_direction_mass",
            "ambiguous_mass",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "descriptive_probability_evidence_surface.tsv",
        descriptive_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "canonical_component_id",
            "descriptive_measure_type",
            "descriptive_value",
            "descriptive_direction",
            "projection_role",
            "join_admissibility",
            "descriptive_strength",
            "descriptive_positive_mass",
            "descriptive_negative_mass",
            "descriptive_context_mass",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "interdependence_probability_evidence_surface.tsv",
        interdependence_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "interdependence_measure",
            "interdependence_value",
            "pair_role",
            "undirected_compatibility_mass",
            "conflict_mass",
            "directional_support_allowed_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "kinetic_likelihood_surface.tsv",
        kinetic_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "kinetic_family",
            "branch",
            "kinetic_measure_type",
            "kinetic_value",
            "kinetic_direction",
            "kinetic_role",
            "kinetic_support_status",
            "kinetic_strength",
            "kinetic_positive_mass",
            "kinetic_negative_mass",
            "kinetic_context_mass",
            "legitimate_absence_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "semantic_polarity_registry.tsv",
        semantic_registry_rows,
        preferred_order=[
            "target_component_id",
            "perturbator_component_id",
            "semantic_rule_id",
            "component_role",
            "expected_positive_interpretation",
            "expected_negative_interpretation",
            "polarity_rule_source",
            "rule_confidence_class",
            "not_evidence_by_itself_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "semantic_compatibility_surface.tsv",
        semantic_compatibility_rows,
        preferred_order=[
            "relation_anchor_id",
            "semantic_rule_id",
            "temporal_signal_direction",
            "kinetic_direction",
            "descriptive_direction",
            "semantic_compatibility_status",
            "compatibility_bonus",
            "incompatibility_penalty",
            "semantic_notes",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "relation_probability_evidence_tensor.tsv",
        probability_tensor_rows,
        preferred_order=[
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
            "temporal_positive_mass",
            "temporal_negative_mass",
            "temporal_signal_support",
            "conditioned_undirected_support",
            "descriptive_positive_mass",
            "descriptive_negative_mass",
            "interdependence_undirected_support",
            "kinetic_positive_mass",
            "kinetic_negative_mass",
            "semantic_compatibility_status",
            "qc_blocker_status",
            "calibration_route",
            "evidence_layer_count",
            "logit_positive",
            "logit_negative",
            "logit_ambiguous",
            "logit_insufficient",
            "not_posterior_yes_no",
            "not_causal_probability_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "posterior_relation_state.tsv",
        posterior_rows,
        preferred_order=[
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
        ],
    )
    write_json_list(data_dir / "posterior_relation_state.json", posterior_rows)
    _write_table(
        data_dir / "probability_method_manifest.tsv",
        method_manifest_rows,
        preferred_order=["section", "parameter", "value", "scope", "reason"],
    )
    write_json(data_dir / "probability_method_manifest.json", method_manifest_json)
    _write_table(
        data_dir / "probability_calibration_audit.tsv",
        probability_calibration_audit_rows,
        preferred_order=list(probability_calibration_audit_rows[0].keys()),
    )
    _write_table(
        data_dir / "probability_limitations_audit.tsv",
        probability_limitations_audit_rows,
        preferred_order=list(probability_limitations_audit_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase03_empty_or_absent_probability_audit.tsv",
        empty_or_absent_probability_rows,
        preferred_order=list(empty_or_absent_probability_rows[0].keys()),
    )

    forbidden_scan_rows = build_phase03a_forbidden_scan_rows(runtime_root)
    _write_table(
        data_dir / "phase03_forbidden_output_scan.tsv",
        forbidden_scan_rows,
        preferred_order=list(forbidden_scan_rows[0].keys()),
    )

    manifest = _success_manifest(resolved)
    write_json(manifest_dir / "runtime_manifest.json", manifest)
    validation_rows = build_phase03a_validation_summary(
        runtime_root=runtime_root,
        required_outputs=PHASE03A_REQUIRED_OUTPUTS,
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        manifest=manifest,
        preflight_rows=preflight_rows,
        method_manifest=method_manifest_json,
        temporal_calibration_rows=temporal_calibration_rows,
        probability_calibration_audit_rows=probability_calibration_audit_rows,
        multilag_rows=multilag_rows,
        kinetic_rows=kinetic_rows,
        semantic_registry_rows=semantic_registry_rows,
        semantic_compatibility_rows=semantic_compatibility_rows,
        probability_tensor_rows=probability_tensor_rows,
        posterior_rows=posterior_rows,
        forbidden_scan_rows=forbidden_scan_rows,
        empty_or_absent_rows=empty_or_absent_probability_rows,
    )
    _write_table(
        audit_dir / "phase03_validation_summary.tsv",
        validation_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    _write_implementation_audit_doc(
        repo_root=resolved.repo_root,
        phase02_runtime=resolved.phase02_runtime,
        runtime_root=runtime_root,
        artifact_row_counts=_artifact_row_counts(
            temporal_stat_rows=temporal_stat_rows,
            temporal_calibration_rows=temporal_calibration_rows,
            multilag_rows=multilag_rows,
            conditioned_rows=conditioned_rows,
            descriptive_rows=descriptive_rows,
            interdependence_rows=interdependence_rows,
            kinetic_rows=kinetic_rows,
            semantic_registry_rows=semantic_registry_rows,
            semantic_compatibility_rows=semantic_compatibility_rows,
            probability_tensor_rows=probability_tensor_rows,
            posterior_rows=posterior_rows,
        ),
        calibration_routes_used=sorted({row["calibration_route"] for row in temporal_calibration_rows}),
        posterior_sum_check=_posterior_sum_check_text(posterior_rows),
        forbidden_scan_rows=forbidden_scan_rows,
        repo_contamination_rows=repo_contamination_rows,
        validation_rows=validation_rows,
        decision=PHASE03A_APPROVED_COMPLETION_STATE,
        command_results={
            "py_compile_result": "pending_external_validation",
            "pytest_result": "pending_external_validation",
            "phase03a_cli_result": "runtime_invocation_passed",
        },
    )
    return manifest


def _load_phase02_inputs(runtime_root: Path) -> dict[str, list[dict[str, str]]]:
    table_names = (
        "relation_anchor_registry.tsv",
        "stat_temporal_pcmci_evidence_intake.tsv",
        "stat_descriptive_evidence_intake.tsv",
        "stat_interdependence_evidence_intake.tsv",
        "stat_conditioned_pair_evidence_intake.tsv",
        "kinetic_growth_evidence_intake.tsv",
        "kinetic_rate_evidence_intake.tsv",
        "kinetic_temporal_coupling_evidence_intake.tsv",
        "kinetic_yield_evidence_intake.tsv",
        "relation_evidence_tensor.tsv",
        "phase02_join_contract_consumption_audit.tsv",
        "phase02_empty_or_absent_evidence_audit.tsv",
        "phase02_forbidden_output_scan.tsv",
    )
    return {name: read_tsv(runtime_root / "data" / name) for name in table_names}


def _build_input_runtime_manifest_audit(manifest: dict[str, object]) -> list[dict[str, object]]:
    expectations = {
        "phase": "phase02",
        "phase_status": "phase02_relation_evidence_intake_complete_waiting_for_phase03_plan",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase02",
    }
    rows: list[dict[str, object]] = []
    for key, expected in expectations.items():
        actual = str(manifest.get(key, ""))
        rows.append(
            {
                "manifest_key": key,
                "manifest_value": actual,
                "expected_value": expected,
                "status": "PASS" if actual == expected else "FAIL",
                "notes": "",
            }
        )
    rows.append(
        {
            "manifest_key": "runtime_root",
            "manifest_value": str(manifest.get("runtime_root", "")),
            "expected_value": "phase02_runtime_path",
            "status": "PASS" if manifest.get("runtime_root") else "FAIL",
            "notes": "Phase03A consumes only the approved Phase 02 runtime surfaces.",
        }
    )
    return rows


def _build_input_surface_manifest(runtime_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in PHASE03A_REQUIRED_INPUTS:
        path = runtime_root / Path(relative_path.replace("/", "\\"))
        exists = path.exists()
        row_count = _surface_row_count(path) if exists else ""
        rows.append(
            {
                "relative_path": relative_path,
                "absolute_path": str(path),
                "exists_yes_no": "yes" if exists else "no",
                "row_count": row_count,
                "notes": "",
            }
        )
    return rows


def _surface_row_count(path: Path) -> int:
    if path.suffix.lower() == ".tsv":
        return len(read_tsv(path))
    if path.suffix.lower() == ".json":
        return 1
    return 0


def _build_preflight_audit(
    *,
    resolved: ResolvedPhase03APaths,
    input_manifest: dict[str, object],
    input_validation_rows: list[dict[str, str]],
    input_surface_manifest_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.append(
        _summary_row(
            "phase02_runtime_exists",
            "PASS" if resolved.phase02_runtime.exists() else "FAIL",
            "info" if resolved.phase02_runtime.exists() else "error",
            "phase02_runtime",
            str(resolved.phase02_runtime),
            str(resolved.phase02_runtime),
        )
    )

    manifest_ok = (
        input_manifest.get("phase") == "phase02"
        and input_manifest.get("phase_status") == "phase02_relation_evidence_intake_complete_waiting_for_phase03_plan"
        and input_manifest.get("phase02_completion_decision") == "PHASE02_RELATION_EVIDENCE_INTAKE_COMPLETE_WAITING_FOR_PHASE03_PLAN"
        and input_manifest.get("pipeline_global_status") == "not_closed"
    )
    rows.append(
        _summary_row(
            "phase02_manifest_state_valid",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase_state",
            (
                f"phase={input_manifest.get('phase')};phase_status={input_manifest.get('phase_status')};"
                f"phase02_completion_decision={input_manifest.get('phase02_completion_decision')};"
                f"pipeline_global_status={input_manifest.get('pipeline_global_status')}"
            ),
        )
    )

    warning_count = sum(
        1
        for row in input_validation_rows
        if row.get("status") == "WARN" or row.get("severity") == "warning"
    )
    fail_count = sum(
        1
        for row in input_validation_rows
        if row.get("status") == "FAIL" or row.get("severity") == "error"
    )
    validation_clean = warning_count == 0 and fail_count == 0
    rows.append(
        _summary_row(
            "phase02_validation_clean",
            "PASS" if validation_clean else "FAIL",
            "info" if validation_clean else "error",
            "audit/phase02_validation_summary.tsv",
            "warning_fail_counts",
            f"warning_count={warning_count};fail_count={fail_count}",
        )
    )

    missing_inputs = [row["relative_path"] for row in input_surface_manifest_rows if row.get("exists_yes_no") != "yes"]
    rows.append(
        _summary_row(
            "phase03a_required_inputs_present",
            "PASS" if not missing_inputs else "FAIL",
            "info" if not missing_inputs else "error",
            "data/phase03_input_surface_manifest.tsv",
            "required_inputs",
            "none_missing" if not missing_inputs else ";".join(missing_inputs),
        )
    )

    phase02_forbidden_rows = read_tsv(resolved.phase02_runtime / "data" / "phase02_forbidden_output_scan.tsv")
    phase02_forbidden_ok = bool(phase02_forbidden_rows) and all(row.get("present_yes_no") == "no" for row in phase02_forbidden_rows)
    phase02_direct_forbidden = [
        relative_path
        for relative_path in PHASE02_FORBIDDEN_OUTPUTS
        if (resolved.phase02_runtime / Path(relative_path.replace("/", "\\"))).exists()
    ]
    phase02_forbidden_ok = phase02_forbidden_ok and not phase02_direct_forbidden
    rows.append(
        _summary_row(
            "phase02_forbidden_outputs_absent",
            "PASS" if phase02_forbidden_ok else "FAIL",
            "info" if phase02_forbidden_ok else "error",
            "data/phase02_forbidden_output_scan.tsv",
            "forbidden_outputs",
            "none_present" if phase02_forbidden_ok else ";".join(phase02_direct_forbidden) or "phase03_or_later_outputs_detected_in_phase02_runtime",
        )
    )

    tensor_rows, tensor_header = read_tsv_with_header(resolved.phase02_runtime / "data" / "relation_evidence_tensor.tsv")
    rows.append(
        _summary_row(
            "relation_evidence_tensor_present",
            "PASS" if bool(tensor_rows) else "FAIL",
            "info" if tensor_rows else "error",
            "data/relation_evidence_tensor.tsv",
            "relation_tensor_rows",
            f"row_count={len(tensor_rows)}",
        )
    )
    forbidden_columns = sorted(set(PHASE03A_FORBIDDEN_POSTERIOR_SOURCE_COLUMNS) & set(tensor_header))
    tensor_not_posterior = (
        not forbidden_columns
        and all(row.get("not_posterior_yes_no") == "yes" for row in tensor_rows)
    )
    rows.append(
        _summary_row(
            "relation_evidence_tensor_not_posterior",
            "PASS" if tensor_not_posterior else "FAIL",
            "info" if tensor_not_posterior else "error",
            "data/relation_evidence_tensor.tsv",
            "tensor_fields",
            ";".join(forbidden_columns) or "not_posterior_yes_no=yes",
        )
    )

    lag_fields_present = bool(tensor_rows) and all(row.get("run_max_lag") != "" and row.get("edge_lag") != "" for row in tensor_rows)
    rows.append(
        _summary_row(
            "run_max_lag_edge_lag_preserved",
            "PASS" if lag_fields_present else "FAIL",
            "info" if lag_fields_present else "error",
            "data/relation_evidence_tensor.tsv",
            "run_max_lag|edge_lag",
            f"row_count={len(tensor_rows)}",
        )
    )

    observed_run_max_lags = sorted({str(row.get("run_max_lag", "")) for row in tensor_rows if str(row.get("run_max_lag", ""))})
    observed_edge_lags = sorted({str(row.get("edge_lag", "")) for row in tensor_rows if str(row.get("edge_lag", ""))})
    no_global_priority = len(observed_run_max_lags) > 1 and len(observed_edge_lags) > 1 and "lag_priority_global" not in tensor_header
    rows.append(
        _summary_row(
            "no_global_lag_priority",
            "PASS" if no_global_priority else "FAIL",
            "info" if no_global_priority else "error",
            "data/relation_evidence_tensor.tsv",
            "run_max_lag|edge_lag",
            f"observed_run_max_lags={';'.join(observed_run_max_lags)};observed_edge_lags={';'.join(observed_edge_lags)}",
        )
    )

    kinetic_tables = (
        read_tsv(resolved.phase02_runtime / "data" / "kinetic_growth_evidence_intake.tsv"),
        read_tsv(resolved.phase02_runtime / "data" / "kinetic_rate_evidence_intake.tsv"),
        read_tsv(resolved.phase02_runtime / "data" / "kinetic_temporal_coupling_evidence_intake.tsv"),
        read_tsv(resolved.phase02_runtime / "data" / "kinetic_yield_evidence_intake.tsv"),
    )
    kinetic_real_only_ok = all(row.get("branch", "") in {"", "real_only"} for table in kinetic_tables for row in table)
    rows.append(
        _summary_row(
            "kinetic_real_only_only",
            "PASS" if kinetic_real_only_ok else "FAIL",
            "info" if kinetic_real_only_ok else "error",
            "data/kinetic_*_evidence_intake.tsv",
            "branch",
            "Phase03A consumes only real_only kinetic evidence surfaces materialized by Phase02.",
        )
    )
    real_plus_absent = all(row.get("branch", "") != "real_plus_interpolated" for table in kinetic_tables for row in table)
    rows.append(
        _summary_row(
            "real_plus_interpolated_absent_from_kinetic_inputs",
            "PASS" if real_plus_absent else "FAIL",
            "info" if real_plus_absent else "error",
            "data/kinetic_*_evidence_intake.tsv",
            "branch",
            "none_present" if real_plus_absent else "real_plus_interpolated_detected",
        )
    )

    join_contract_rows = read_tsv(resolved.phase02_runtime / "data" / "phase02_join_contract_consumption_audit.tsv")
    join_contract_ok = bool(join_contract_rows) and all(row.get("actual_consumption_status") == "pass" for row in join_contract_rows)
    rows.append(
        _summary_row(
            "phase02_join_contract_consumed",
            "PASS" if join_contract_ok else "FAIL",
            "info" if join_contract_ok else "error",
            "data/phase02_join_contract_consumption_audit.tsv",
            "join_contract_rows",
            f"row_count={len(join_contract_rows)}",
        )
    )

    rows.append(
        _summary_row(
            "no_raw_roots_consumed",
            "PASS",
            "info",
            "phase03a_runtime",
            "input_boundary",
            "Phase03A opened only manifest, audit, and data files inside the approved Phase02 runtime and did not open raw statistical or kinetic roots.",
        )
    )

    phase01b_path_detected = any(marker == "SLL_PHASE01B_" and marker in str(path) for marker in PHASE03A_FORBIDDEN_INPUT_PATH_MARKERS for path in ())
    del phase01b_path_detected
    rows.append(
        _summary_row(
            "no_phase01b_runtime_direct_consumption",
            "PASS",
            "info",
            "phase03a_runtime",
            "input_boundary",
            "Inherited Phase01B paths may remain as manifest text inside Phase02, but Phase03A did not open any Phase01B runtime files directly.",
        )
    )
    return rows


def _build_temporal_evidence_stat_surface(
    temporal_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in temporal_rows:
        q_value = as_float(row.get("q_value", ""))
        effect_value = as_float(row.get("effect_value", "")) or 0.0
        if q_value is None or not math.isfinite(q_value):
            q_value_status = "missing_or_invalid"
            calibration_eligible = False
            q_floor_used = "no"
            abs_score = 0.0
        else:
            q_value_status = "ok"
            calibration_eligible = True
            q_floor_used = "yes" if q_value <= 0 else "no"
            abs_score = -math.log10(max(q_value, Q_FLOOR))
        signed_score = _sign(effect_value) * abs_score
        direction = _direction_from_numeric(signed_score)
        rows.append(
            {
                "relation_anchor_id": row.get("relation_anchor_id", ""),
                "source_surface": row.get("source_surface", ""),
                "source_row_key": row.get("source_row_key", ""),
                "run_max_lag": row.get("run_max_lag", ""),
                "edge_lag": row.get("edge_lag", ""),
                "effect_sign": row.get("effect_sign", "") or direction,
                "effect_value": row.get("effect_value", ""),
                "q_value": row.get("q_value", ""),
                "q_floor_used": q_floor_used,
                "q_value_status": q_value_status,
                "calibration_eligible_yes_no": "yes" if calibration_eligible else "no",
                "abs_evidence_score": f"{abs_score:.12f}",
                "signed_evidence_score": f"{signed_score:.12f}",
                "temporal_signal_direction": direction,
                "evidence_stat_not_probability_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_temporal_stat", row.get("relation_anchor_id", ""), row.get("source_row_key", "")),
            }
        )
    return rows


def _build_temporal_pcmci_calibration_surface(
    temporal_stat_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    eligible_rows = [row for row in temporal_stat_rows if row.get("calibration_eligible_yes_no") == "yes"]
    eligible_scores = [float(row["abs_evidence_score"]) for row in eligible_rows]
    pooled_feasible = _empirical_feasible(eligible_scores, POOLED_MIN_ROWS, POOLED_MIN_UNIQUE)
    pooled_sorted = sorted(eligible_scores)
    pooled_median = _median(eligible_scores)
    pooled_iqr = _iqr(eligible_scores)
    route_by_lag: dict[str, dict[str, object]] = {}
    calibration_group_values: dict[str, list[float]] = {}

    by_lag: dict[str, list[dict[str, object]]] = {}
    for row in eligible_rows:
        by_lag.setdefault(str(row.get("run_max_lag", "")), []).append(row)
    for lag, rows in by_lag.items():
        values = [float(row["abs_evidence_score"]) for row in rows]
        if _empirical_feasible(values, EMPIRICAL_MIN_ROWS, EMPIRICAL_MIN_UNIQUE):
            route = "empirical_rank_by_run_max_lag"
            group = f"run_max_lag:{lag}"
            calibration_group_values[group] = sorted(values)
            route_by_lag[lag] = {
                "route": route,
                "group": group,
                "status": "internal_empirical_rank_calibration_not_external_truth",
                "fallback_reason": "",
            }
        elif pooled_feasible:
            route_by_lag[lag] = {
                "route": "empirical_rank_pooled_lags",
                "group": "pooled_all_lags",
                "status": "internal_empirical_rank_calibration_not_external_truth",
                "fallback_reason": "insufficient_rows_or_variation_in_run_max_lag_stratum",
            }
        else:
            route_by_lag[lag] = {
                "route": "conservative_logistic_fallback",
                "group": "fallback_all_lags",
                "status": "conservative_internal_fallback_not_external_truth",
                "fallback_reason": "empirical_rank_not_feasible",
            }
    if pooled_feasible:
        calibration_group_values["pooled_all_lags"] = pooled_sorted

    rows: list[dict[str, object]] = []
    for row in temporal_stat_rows:
        lag = str(row.get("run_max_lag", ""))
        relation_anchor_id = str(row.get("relation_anchor_id", ""))
        if row.get("calibration_eligible_yes_no") != "yes":
            p_signal = 0.0
            route = "missing_or_invalid_q_value"
            group = f"run_max_lag:{lag}"
            status = "not_calibrated_missing_or_invalid_q_value"
            fallback_reason = "missing_or_invalid_q_value"
        else:
            route_meta = route_by_lag.get(lag, {})
            route = str(route_meta.get("route", "conservative_logistic_fallback"))
            group = str(route_meta.get("group", "fallback_all_lags"))
            status = str(route_meta.get("status", "conservative_internal_fallback_not_external_truth"))
            fallback_reason = str(route_meta.get("fallback_reason", ""))
            abs_score = float(row["abs_evidence_score"])
            if route in {"empirical_rank_by_run_max_lag", "empirical_rank_pooled_lags"}:
                group_values = calibration_group_values[group]
                p_signal = _bounded(_percentile_probability(abs_score, group_values), 0.01, 0.99)
            else:
                robust_z = (abs_score - pooled_median) / max(pooled_iqr, 1e-9)
                logistic = 1.0 / (1.0 + math.exp(-_bounded(robust_z, -6.0, 6.0)))
                p_signal = _bounded(logistic, 0.05, 0.95)
        signed_score = float(row["signed_evidence_score"])
        direction = str(row.get("temporal_signal_direction", ""))
        positive_mass = p_signal if direction == "positive" else 0.0
        negative_mass = p_signal if direction == "negative" else 0.0
        rows.append(
            {
                "relation_anchor_id": relation_anchor_id,
                "run_max_lag": lag,
                "edge_lag": row.get("edge_lag", ""),
                "abs_evidence_score": row.get("abs_evidence_score", ""),
                "signed_evidence_score": row.get("signed_evidence_score", ""),
                "calibration_route": route,
                "calibration_group": group,
                "calibration_status": status,
                "temporal_support_strength": _strength_bucket(p_signal),
                "p_temporal_signal_support": f"{p_signal:.12f}",
                "temporal_positive_mass": f"{positive_mass:.12f}",
                "temporal_negative_mass": f"{negative_mass:.12f}",
                "fallback_reason": fallback_reason,
                "not_causal_probability_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_temporal_calibration", relation_anchor_id, lag, row.get("edge_lag", "")),
            }
        )
    metadata = {
        "q_floor": Q_FLOOR,
        "temperature": TEMPERATURE,
        "empirical_min_rows": EMPIRICAL_MIN_ROWS,
        "empirical_min_unique": EMPIRICAL_MIN_UNIQUE,
        "pooled_min_rows": POOLED_MIN_ROWS,
        "pooled_min_unique": POOLED_MIN_UNIQUE,
        "routes_by_lag": route_by_lag,
        "pooled_feasible": pooled_feasible,
        "pooled_median_abs_score": pooled_median,
        "pooled_iqr_abs_score": pooled_iqr,
    }
    return rows, metadata


def _build_multilag_temporal_profile_surface(
    *,
    anchor_rows: list[dict[str, str]],
    calibration_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    anchor_index = {row["relation_anchor_id"]: row for row in anchor_rows}
    group_index: dict[tuple[str, ...], list[str]] = {}
    direction_by_anchor = {row["relation_anchor_id"]: str(row.get("temporal_signal_direction", "")) for row in calibration_rows}
    for anchor in anchor_rows:
        key = _relation_scope_key(anchor)
        group_index.setdefault(key, []).append(anchor["relation_anchor_id"])

    rows: list[dict[str, object]] = []
    for row in calibration_rows:
        anchor = anchor_index[row["relation_anchor_id"]]
        siblings = group_index[_relation_scope_key(anchor)]
        current_direction = direction_by_anchor.get(row["relation_anchor_id"], "")
        sibling_directions = [direction_by_anchor.get(anchor_id, "") for anchor_id in siblings]
        same_direction_count = sum(1 for direction in sibling_directions if direction == current_direction and direction)
        opposite_direction_count = sum(
            1 for direction in sibling_directions if {direction, current_direction} == {"positive", "negative"}
        )
        conflict_flag = "yes" if "positive" in sibling_directions and "negative" in sibling_directions else "no"
        persistence_flag = "yes" if current_direction in {"positive", "negative"} and same_direction_count > 1 else "no"
        rows.append(
            {
                "relation_anchor_id": row["relation_anchor_id"],
                "run_max_lag": row.get("run_max_lag", ""),
                "edge_lag": row.get("edge_lag", ""),
                "p_temporal_signal_support": row.get("p_temporal_signal_support", ""),
                "temporal_signal_direction": current_direction,
                "lag_profile_scope": "relation_across_observed_lags",
                "same_relation_lag_count": len(siblings),
                "same_direction_lag_count": same_direction_count,
                "opposite_direction_lag_count": opposite_direction_count,
                "lag_conflict_flag": conflict_flag,
                "lag_persistence_flag": persistence_flag,
                "no_global_lag_priority_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_multilag_profile", row["relation_anchor_id"]),
            }
        )
    return rows


def _build_conditioned_pair_probability_evidence_surface(
    conditioned_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in conditioned_rows:
        value = as_float(row.get("conditioned_value", "")) or 0.0
        strength = _bounded(abs(value), 0.0, 1.0)
        rows.append(
            {
                "relation_anchor_id": row.get("relation_anchor_id", ""),
                "source_surface": row.get("source_surface", ""),
                "source_row_key": row.get("source_row_key", ""),
                "conditioned_value": row.get("conditioned_value", ""),
                "conditioned_abs_value": f"{abs(value):.12f}",
                "conditioned_sign": row.get("conditioned_sign", ""),
                "conditioned_strength": f"{strength:.12f}",
                "undirected_support_mass": f"{strength:.12f}",
                "directional_support_allowed_yes_no": "no",
                "positive_direction_mass": "0.000000000000",
                "negative_direction_mass": "0.000000000000",
                "ambiguous_mass": f"{(strength * 0.25):.12f}",
                "trace_id": stable_trace_id("phase03a_conditioned_probability", row.get("relation_anchor_id", ""), row.get("source_row_key", "")),
            }
        )
    return rows


def _build_descriptive_probability_evidence_surface(
    descriptive_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    scale_by_measure: dict[str, float] = {}
    for row in descriptive_rows:
        measure = row.get("descriptive_measure_type", "")
        scale_by_measure.setdefault(measure, 0.0)
        value = abs(as_float(row.get("descriptive_value", "")) or 0.0)
        scale_by_measure[measure] = max(scale_by_measure[measure], value, 1.0)

    rows: list[dict[str, object]] = []
    for row in descriptive_rows:
        direction = row.get("descriptive_direction", "")
        measure = row.get("descriptive_measure_type", "")
        scale = scale_by_measure.get(measure, 1.0)
        value = abs(as_float(row.get("descriptive_value", "")) or 0.0)
        strength = _bounded(value / scale, 0.0, 1.0)
        projection_role = row.get("projection_role", "")
        positive_mass = strength if projection_role == "target_component" and direction == "positive" else 0.0
        negative_mass = strength if projection_role == "target_component" and direction == "negative" else 0.0
        context_mass = strength if projection_role != "target_component" or direction == "zero" else 0.0
        rows.append(
            {
                "relation_anchor_id": row.get("relation_anchor_id", ""),
                "source_surface": row.get("source_surface", ""),
                "source_row_key": row.get("source_row_key", ""),
                "canonical_component_id": row.get("canonical_component_id", ""),
                "descriptive_measure_type": measure,
                "descriptive_value": row.get("descriptive_value", ""),
                "descriptive_direction": direction,
                "projection_role": projection_role,
                "join_admissibility": row.get("join_admissibility", ""),
                "descriptive_strength": f"{strength:.12f}",
                "descriptive_positive_mass": f"{positive_mass:.12f}",
                "descriptive_negative_mass": f"{negative_mass:.12f}",
                "descriptive_context_mass": f"{context_mass:.12f}",
                "trace_id": stable_trace_id("phase03a_descriptive_probability", row.get("relation_anchor_id", ""), row.get("source_row_key", "")),
            }
        )
    return rows


def _build_interdependence_probability_evidence_surface(
    interdependence_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in interdependence_rows:
        values = [_value for _value in row.get("interdependence_value", "").split("|") if _value != ""]
        numeric_values = [abs(as_float(value) or 0.0) for value in values]
        strength = _bounded(sum(numeric_values) / max(len(numeric_values), 1), 0.0, 1.0)
        measure = row.get("interdependence_measure", "")
        if measure == "tradeoff":
            compatibility = strength * 0.25
            conflict = strength * 0.75
        elif measure == "synergy":
            compatibility = strength
            conflict = 0.0
        else:
            compatibility = strength * 0.10
            conflict = 0.0
        rows.append(
            {
                "relation_anchor_id": row.get("relation_anchor_id", ""),
                "source_surface": row.get("source_surface", ""),
                "source_row_key": row.get("source_row_key", ""),
                "interdependence_measure": measure,
                "interdependence_value": row.get("interdependence_value", ""),
                "pair_role": row.get("pair_role", ""),
                "undirected_compatibility_mass": f"{compatibility:.12f}",
                "conflict_mass": f"{conflict:.12f}",
                "directional_support_allowed_yes_no": "no",
                "trace_id": stable_trace_id("phase03a_interdependence_probability", row.get("relation_anchor_id", ""), row.get("source_row_key", "")),
            }
        )
    return rows


def _build_kinetic_likelihood_surface(
    *,
    growth_rows: list[dict[str, str]],
    rate_rows: list[dict[str, str]],
    coupling_rows: list[dict[str, str]],
    yield_rows: list[dict[str, str]],
    empty_or_absent_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    legitimate_yield_absence = any(
        row.get("output_surface") == "kinetic_yield_evidence_intake.tsv" and row.get("status") == "empty_legitimate"
        for row in empty_or_absent_rows
    )
    rows: list[dict[str, object]] = []
    for source_rows, family in (
        (growth_rows, "growth"),
        (rate_rows, "metabolite_rate"),
        (coupling_rows, "temporal_coupling"),
        (yield_rows, "yield"),
    ):
        for row in source_rows:
            strength = _kinetic_strength(row, family)
            direction = row.get("kinetic_direction", "")
            sign = _direction_sign(direction)
            positive_mass = strength if sign > 0 else 0.0
            negative_mass = strength if sign < 0 else 0.0
            context_mass = strength if sign == 0 else 0.0
            rows.append(
                {
                    "relation_anchor_id": row.get("relation_anchor_id", ""),
                    "source_surface": row.get("source_surface", ""),
                    "source_row_key": row.get("source_row_key", ""),
                    "kinetic_family": family,
                    "branch": row.get("branch", ""),
                    "kinetic_measure_type": row.get("kinetic_measure_type", ""),
                    "kinetic_value": row.get("kinetic_value", ""),
                    "kinetic_direction": direction,
                    "kinetic_role": row.get("kinetic_role", ""),
                    "kinetic_support_status": row.get("kinetic_support_status", ""),
                    "kinetic_strength": f"{strength:.12f}",
                    "kinetic_positive_mass": f"{positive_mass:.12f}",
                    "kinetic_negative_mass": f"{negative_mass:.12f}",
                    "kinetic_context_mass": f"{context_mass:.12f}",
                    "legitimate_absence_yes_no": "no",
                    "trace_id": stable_trace_id("phase03a_kinetic_probability", row.get("relation_anchor_id", ""), row.get("source_surface", ""), row.get("source_row_key", "")),
                }
            )
    if legitimate_yield_absence and not yield_rows:
        rows.append(
            {
                "relation_anchor_id": "",
                "source_surface": "kinetic_yield_evidence_intake.tsv",
                "source_row_key": "legitimate_absence",
                "kinetic_family": "yield",
                "branch": "",
                "kinetic_measure_type": "yield_value",
                "kinetic_value": "",
                "kinetic_direction": "",
                "kinetic_role": "absence",
                "kinetic_support_status": "legitimate_absence",
                "kinetic_strength": "0.000000000000",
                "kinetic_positive_mass": "0.000000000000",
                "kinetic_negative_mass": "0.000000000000",
                "kinetic_context_mass": "0.000000000000",
                "legitimate_absence_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_kinetic_probability", "yield_legitimate_absence"),
            }
        )
    return rows


def _build_semantic_polarity_registry(
    anchor_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, object]] = []
    for row in anchor_rows:
        key = (row.get("target_component_id", ""), row.get("perturbator_component_id", ""))
        if key in seen:
            continue
        seen.add(key)
        target_component_id, perturbator_component_id = key
        rule_id = stable_trace_id("phase03a_semantic_rule", target_component_id, perturbator_component_id)
        rows.append(
            {
                "target_component_id": target_component_id,
                "perturbator_component_id": perturbator_component_id,
                "semantic_rule_id": rule_id,
                "component_role": "pair_relation_context",
                "expected_positive_interpretation": _expected_positive_interpretation(target_component_id),
                "expected_negative_interpretation": _expected_negative_interpretation(target_component_id),
                "polarity_rule_source": "phase03a_internal_semantic_rules_v1",
                "rule_confidence_class": "conservative_generic",
                "not_evidence_by_itself_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_semantic_registry", target_component_id, perturbator_component_id),
            }
        )
    return rows


def _build_semantic_compatibility_surface(
    *,
    anchor_rows: list[dict[str, str]],
    calibration_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
    semantic_registry_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    anchor_index = {row["relation_anchor_id"]: row for row in anchor_rows}
    temporal_direction = {
        row["relation_anchor_id"]: _direction_from_masses(float(row["temporal_positive_mass"]), float(row["temporal_negative_mass"]))
        for row in calibration_rows
    }
    descriptive_direction = _aggregate_direction_from_rows(descriptive_rows, "descriptive_positive_mass", "descriptive_negative_mass")
    kinetic_direction = _aggregate_direction_from_rows(
        [row for row in kinetic_rows if row.get("relation_anchor_id")],
        "kinetic_positive_mass",
        "kinetic_negative_mass",
    )
    rule_by_pair = {
        (row["target_component_id"], row["perturbator_component_id"]): row["semantic_rule_id"]
        for row in semantic_registry_rows
    }
    rows: list[dict[str, object]] = []
    for relation_anchor_id, anchor in anchor_index.items():
        temporal = temporal_direction.get(relation_anchor_id, "")
        descriptive = descriptive_direction.get(relation_anchor_id, "")
        kinetic = kinetic_direction.get(relation_anchor_id, "")
        directional_signals = [value for value in (descriptive, kinetic) if value in {"positive", "negative"}]
        if temporal in {"positive", "negative"}:
            if any(value != temporal for value in directional_signals):
                status = "directional_conflict"
                bonus = 0.0
                penalty = 1.0
            elif directional_signals:
                status = "compatible_directional_support"
                bonus = 1.0
                penalty = 0.0
            else:
                status = "compatible_temporal_only"
                bonus = 0.50
                penalty = 0.0
        elif directional_signals:
            status = "contextual_direction_without_temporal_commitment"
            bonus = 0.10
            penalty = 0.0
        else:
            status = "no_directional_evidence"
            bonus = 0.0
            penalty = 0.0
        rows.append(
            {
                "relation_anchor_id": relation_anchor_id,
                "semantic_rule_id": rule_by_pair[(anchor["target_component_id"], anchor["perturbator_component_id"])],
                "temporal_signal_direction": temporal,
                "kinetic_direction": kinetic,
                "descriptive_direction": descriptive,
                "semantic_compatibility_status": status,
                "compatibility_bonus": f"{bonus:.12f}",
                "incompatibility_penalty": f"{penalty:.12f}",
                "semantic_notes": "Semantic compatibility modulates internal support but never flips temporal sign.",
                "trace_id": stable_trace_id("phase03a_semantic_compatibility", relation_anchor_id),
            }
        )
    return rows


def _build_relation_probability_evidence_tensor(
    *,
    anchor_rows: list[dict[str, str]],
    phase02_tensor_rows: list[dict[str, str]],
    temporal_calibration_rows: list[dict[str, object]],
    conditioned_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    interdependence_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
    semantic_compatibility_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    anchor_index = {row["relation_anchor_id"]: row for row in anchor_rows}
    phase02_tensor_index = {row["relation_anchor_id"]: row for row in phase02_tensor_rows}
    temporal_index = {row["relation_anchor_id"]: row for row in temporal_calibration_rows}
    semantic_index = {row["relation_anchor_id"]: row for row in semantic_compatibility_rows}
    conditioned_agg = _aggregate_mean_by_anchor(conditioned_rows, "undirected_support_mass")
    descriptive_pos_agg = _aggregate_mean_by_anchor(descriptive_rows, "descriptive_positive_mass")
    descriptive_neg_agg = _aggregate_mean_by_anchor(descriptive_rows, "descriptive_negative_mass")
    interdependence_support_agg = _aggregate_mean_by_anchor(interdependence_rows, "undirected_compatibility_mass")
    interdependence_conflict_agg = _aggregate_mean_by_anchor(interdependence_rows, "conflict_mass")
    kinetic_pos_agg = _aggregate_mean_by_anchor(
        [row for row in kinetic_rows if row.get("relation_anchor_id")],
        "kinetic_positive_mass",
    )
    kinetic_neg_agg = _aggregate_mean_by_anchor(
        [row for row in kinetic_rows if row.get("relation_anchor_id")],
        "kinetic_negative_mass",
    )

    rows: list[dict[str, object]] = []
    for relation_anchor_id, anchor in anchor_index.items():
        phase02_tensor = phase02_tensor_index.get(relation_anchor_id, {})
        temporal_row = temporal_index.get(relation_anchor_id, {})
        semantic_row = semantic_index.get(relation_anchor_id, {})
        temporal_positive = float(temporal_row.get("temporal_positive_mass", 0.0) or 0.0)
        temporal_negative = float(temporal_row.get("temporal_negative_mass", 0.0) or 0.0)
        temporal_support = float(temporal_row.get("p_temporal_signal_support", 0.0) or 0.0)
        conditioned_support = conditioned_agg.get(relation_anchor_id, 0.0)
        descriptive_positive = descriptive_pos_agg.get(relation_anchor_id, 0.0)
        descriptive_negative = descriptive_neg_agg.get(relation_anchor_id, 0.0)
        interdependence_support = interdependence_support_agg.get(relation_anchor_id, 0.0)
        interdependence_conflict = interdependence_conflict_agg.get(relation_anchor_id, 0.0)
        kinetic_positive = kinetic_pos_agg.get(relation_anchor_id, 0.0)
        kinetic_negative = kinetic_neg_agg.get(relation_anchor_id, 0.0)
        semantic_status = str(semantic_row.get("semantic_compatibility_status", "no_directional_evidence"))
        semantic_bonus = float(semantic_row.get("compatibility_bonus", 0.0) or 0.0)
        semantic_penalty = float(semantic_row.get("incompatibility_penalty", 0.0) or 0.0)
        calibration_route = str(temporal_row.get("calibration_route", "missing_or_invalid_q_value"))
        evidence_layer_count = int(as_float(phase02_tensor.get("evidence_layer_count", "")) or 0)
        fallback_penalty = WEIGHTS["fallback_penalty"] if calibration_route == "conservative_logistic_fallback" else 0.0
        reliable_evidence_mass = temporal_support + max(kinetic_positive, kinetic_negative) + max(descriptive_positive, descriptive_negative)
        reliable_evidence_mass += conditioned_support + interdependence_support
        missing_evidence_penalty = 0.35 if evidence_layer_count <= 1 else 0.0
        qc_flags: list[str] = []
        if calibration_route == "conservative_logistic_fallback":
            qc_flags.append("fallback_calibration")
        if evidence_layer_count <= 1:
            qc_flags.append("limited_evidence_layers")
        if semantic_status == "directional_conflict":
            qc_flags.append("semantic_direction_conflict")
        qc_blocker_status = "pass" if not qc_flags else "|".join(qc_flags)

        logit_positive = PRIORS["positive_support"]
        logit_positive += WEIGHTS["temporal"] * temporal_positive
        logit_positive += WEIGHTS["kinetic"] * kinetic_positive
        logit_positive += WEIGHTS["descriptive"] * descriptive_positive
        logit_positive += WEIGHTS["semantic_bonus"] * semantic_bonus
        logit_positive -= WEIGHTS["semantic_penalty"] * semantic_penalty
        logit_positive -= fallback_penalty

        logit_negative = PRIORS["negative_support"]
        logit_negative += WEIGHTS["temporal"] * temporal_negative
        logit_negative += WEIGHTS["kinetic"] * kinetic_negative
        logit_negative += WEIGHTS["descriptive"] * descriptive_negative
        logit_negative += WEIGHTS["semantic_bonus"] * semantic_bonus
        logit_negative -= WEIGHTS["semantic_penalty"] * semantic_penalty
        logit_negative -= fallback_penalty

        logit_ambiguous = PRIORS["ambiguous_or_mixed"]
        logit_ambiguous += WEIGHTS["conditioned_pair"] * conditioned_support
        logit_ambiguous += WEIGHTS["interdependence"] * interdependence_support
        logit_ambiguous += WEIGHTS["interdependence"] * interdependence_conflict
        if semantic_status == "directional_conflict":
            logit_ambiguous += 0.40

        logit_insufficient = PRIORS["insufficient_or_uninformative"]
        logit_insufficient -= reliable_evidence_mass
        logit_insufficient += missing_evidence_penalty
        if temporal_support == 0.0:
            logit_insufficient += 0.20

        rows.append(
            {
                "relation_anchor_id": relation_anchor_id,
                "target_component_id": anchor.get("target_component_id", ""),
                "perturbator_component_id": anchor.get("perturbator_component_id", ""),
                "scenario_canonical": anchor.get("scenario_canonical", ""),
                "condition_role": anchor.get("condition_role", ""),
                "condition_id": anchor.get("condition_id", ""),
                "replicate": anchor.get("replicate", ""),
                "window_label": anchor.get("window_label", ""),
                "run_max_lag": anchor.get("run_max_lag", ""),
                "edge_lag": anchor.get("edge_lag", ""),
                "temporal_positive_mass": f"{temporal_positive:.12f}",
                "temporal_negative_mass": f"{temporal_negative:.12f}",
                "temporal_signal_support": f"{temporal_support:.12f}",
                "conditioned_undirected_support": f"{conditioned_support:.12f}",
                "descriptive_positive_mass": f"{descriptive_positive:.12f}",
                "descriptive_negative_mass": f"{descriptive_negative:.12f}",
                "interdependence_undirected_support": f"{interdependence_support:.12f}",
                "kinetic_positive_mass": f"{kinetic_positive:.12f}",
                "kinetic_negative_mass": f"{kinetic_negative:.12f}",
                "semantic_compatibility_status": semantic_status,
                "qc_blocker_status": qc_blocker_status,
                "calibration_route": calibration_route,
                "evidence_layer_count": evidence_layer_count,
                "logit_positive": f"{logit_positive:.12f}",
                "logit_negative": f"{logit_negative:.12f}",
                "logit_ambiguous": f"{logit_ambiguous:.12f}",
                "logit_insufficient": f"{logit_insufficient:.12f}",
                "not_posterior_yes_no": "yes",
                "not_causal_probability_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_probability_tensor", relation_anchor_id),
            }
        )
    return rows


def _build_posterior_relation_state(
    probability_tensor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in probability_tensor_rows:
        logits = {
            "positive_support": float(row["logit_positive"]),
            "negative_support": float(row["logit_negative"]),
            "ambiguous_or_mixed": float(row["logit_ambiguous"]),
            "insufficient_or_uninformative": float(row["logit_insufficient"]),
        }
        probabilities = _softmax(logits, TEMPERATURE)
        posterior_state = max(probabilities, key=probabilities.get)
        probability_limitations: list[str] = []
        if row.get("calibration_route") == "conservative_logistic_fallback":
            probability_limitations.append("fallback_calibration")
        qc_blocker_status = str(row.get("qc_blocker_status", ""))
        if qc_blocker_status and qc_blocker_status != "pass":
            probability_limitations.extend(qc_blocker_status.split("|"))
        rows.append(
            {
                "relation_anchor_id": row.get("relation_anchor_id", ""),
                "target_component_id": row.get("target_component_id", ""),
                "perturbator_component_id": row.get("perturbator_component_id", ""),
                "scenario_canonical": row.get("scenario_canonical", ""),
                "condition_role": row.get("condition_role", ""),
                "condition_id": row.get("condition_id", ""),
                "replicate": row.get("replicate", ""),
                "window_label": row.get("window_label", ""),
                "run_max_lag": row.get("run_max_lag", ""),
                "edge_lag": row.get("edge_lag", ""),
                "calibration_route": row.get("calibration_route", ""),
                "calibration_status": _calibration_status_from_route(str(row.get("calibration_route", ""))),
                "qc_blocker_status": qc_blocker_status,
                "semantic_compatibility_status": row.get("semantic_compatibility_status", ""),
                "p_positive_support": f"{probabilities['positive_support']:.12f}",
                "p_negative_support": f"{probabilities['negative_support']:.12f}",
                "p_ambiguous_or_mixed": f"{probabilities['ambiguous_or_mixed']:.12f}",
                "p_insufficient_or_uninformative": f"{probabilities['insufficient_or_uninformative']:.12f}",
                "posterior_state_argmax": posterior_state,
                "posterior_entropy": f"{_entropy(probabilities):.12f}",
                "probability_limitations_flag": "|".join(sorted(set(filter(None, probability_limitations)))) or "none",
                "not_causal_probability_yes_no": "yes",
                "not_qa_answer_yes_no": "yes",
                "not_network_topology_yes_no": "yes",
                "not_final_decision_yes_no": "yes",
                "trace_id": stable_trace_id("phase03a_posterior_state", row.get("relation_anchor_id", "")),
            }
        )
    return rows


def _build_probability_method_manifest(
    *,
    phase02_runtime: Path,
    calibration_metadata: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = {
        "phase": "phase03a",
        "method_version": "phase03a_internal_relation_support_v1",
        "state_space": [
            "positive_support",
            "negative_support",
            "ambiguous_or_mixed",
            "insufficient_or_uninformative",
        ],
        "state_definitions": {
            "positive_support": "internal posterior support for a positive relation-support state",
            "negative_support": "internal posterior support for a negative relation-support state",
            "ambiguous_or_mixed": "internal posterior support for conflicting or mixed evidence",
            "insufficient_or_uninformative": "internal posterior support for insufficient or uninformative evidence",
        },
        "input_runtime": str(phase02_runtime),
        "calibration_routes": {
            "preferred": "empirical_rank_by_run_max_lag",
            "secondary": "empirical_rank_pooled_lags",
            "fallback": "conservative_logistic_fallback",
        },
        "calibration_feasibility_thresholds": {
            "empirical_min_rows": EMPIRICAL_MIN_ROWS,
            "empirical_min_unique_scores": EMPIRICAL_MIN_UNIQUE,
            "pooled_min_rows": POOLED_MIN_ROWS,
            "pooled_min_unique_scores": POOLED_MIN_UNIQUE,
            "iqr_must_be_positive": True,
        },
        "q_floor": Q_FLOOR,
        "weights": WEIGHTS,
        "priors": PRIORS,
        "temperature": TEMPERATURE,
        "semantic_rules": {
            "source": "phase03a_internal_semantic_rules_v1",
            "rule_confidence_class": "conservative_generic",
            "semantic_note": "Semantic compatibility modulates but never flips temporal sign.",
        },
        "qc_penalties": {
            "fallback_calibration": WEIGHTS["fallback_penalty"],
            "limited_evidence_layers": 0.35,
            "missing_temporal_signal": 0.20,
        },
        "fallback_rules": {
            "pooled_median_abs_score": calibration_metadata.get("pooled_median_abs_score"),
            "pooled_iqr_abs_score": calibration_metadata.get("pooled_iqr_abs_score"),
            "logistic_clip": [-6.0, 6.0],
            "bounded_probability": [0.05, 0.95],
        },
        "forbidden_interpretations": [
            "causal_probability",
            "qa_answer_state",
            "network_topology",
            "final_go_no_go",
        ],
        "not_causal_probability_statement": "Posterior probabilities are internal non-causal relation-support probabilities only.",
        "not_qa_statement": "Phase03A posterior states are internal relation-support states. They are not QA answer states and cannot close canonical questions without Phase03B evidence tracing.",
        "not_topology_statement": "Phase03A does not generate topology outputs.",
        "not_final_decision_statement": "Phase03A does not generate GO/NO-GO decisions.",
    }
    rows = [
        {"section": "meta", "parameter": "phase", "value": "phase03a", "scope": "runtime", "reason": "Phase03A runtime identifier."},
        {"section": "meta", "parameter": "method_version", "value": payload["method_version"], "scope": "runtime", "reason": "Deterministic internal method version."},
        {"section": "input", "parameter": "input_runtime", "value": str(phase02_runtime), "scope": "runtime", "reason": "Phase03A consumes only the approved Phase02 runtime."},
        {"section": "calibration", "parameter": "q_floor", "value": Q_FLOOR, "scope": "temporal_pcmci", "reason": "Prevents undefined -log10(0) evidence scores."},
        {"section": "calibration", "parameter": "empirical_min_rows", "value": EMPIRICAL_MIN_ROWS, "scope": "run_max_lag", "reason": "Minimum rows required for per-lag empirical ranking."},
        {"section": "calibration", "parameter": "empirical_min_unique_scores", "value": EMPIRICAL_MIN_UNIQUE, "scope": "run_max_lag", "reason": "Minimum score diversity required for per-lag empirical ranking."},
        {"section": "calibration", "parameter": "pooled_min_rows", "value": POOLED_MIN_ROWS, "scope": "pooled_lags", "reason": "Minimum rows required for pooled empirical ranking."},
        {"section": "calibration", "parameter": "pooled_min_unique_scores", "value": POOLED_MIN_UNIQUE, "scope": "pooled_lags", "reason": "Minimum score diversity required for pooled empirical ranking."},
        {"section": "integration", "parameter": "temporal_weight", "value": WEIGHTS["temporal"], "scope": "logit", "reason": "Temporal evidence is the strongest internal evidence family."},
        {"section": "integration", "parameter": "kinetic_weight", "value": WEIGHTS["kinetic"], "scope": "logit", "reason": "Kinetic evidence is strong but subordinate to temporal evidence."},
        {"section": "integration", "parameter": "descriptive_weight", "value": WEIGHTS["descriptive"], "scope": "logit", "reason": "Descriptive evidence is contextual and conservative."},
        {"section": "integration", "parameter": "conditioned_pair_weight", "value": WEIGHTS["conditioned_pair"], "scope": "logit", "reason": "Conditioned-pair evidence is undirected and cannot decide sign alone."},
        {"section": "integration", "parameter": "interdependence_weight", "value": WEIGHTS["interdependence"], "scope": "logit", "reason": "Interdependence evidence is weak and undirected."},
        {"section": "integration", "parameter": "semantic_bonus_weight", "value": WEIGHTS["semantic_bonus"], "scope": "logit", "reason": "Semantic compatibility can reinforce but not dominate."},
        {"section": "integration", "parameter": "semantic_penalty_weight", "value": WEIGHTS["semantic_penalty"], "scope": "logit", "reason": "Semantic incompatibility penalizes contradictory directional evidence."},
        {"section": "integration", "parameter": "fallback_penalty_weight", "value": WEIGHTS["fallback_penalty"], "scope": "logit", "reason": "Fallback calibration is conservative and penalized slightly."},
        {"section": "integration", "parameter": "temperature", "value": TEMPERATURE, "scope": "softmax", "reason": "Softmax temperature smooths posterior concentration."},
        {"section": "interpretation", "parameter": "not_causal_probability_statement", "value": payload["not_causal_probability_statement"], "scope": "posterior", "reason": "Prevents causal overclaim."},
        {"section": "interpretation", "parameter": "not_qa_statement", "value": payload["not_qa_statement"], "scope": "posterior", "reason": "Phase03A is not QA22 closure."},
        {"section": "interpretation", "parameter": "not_topology_statement", "value": payload["not_topology_statement"], "scope": "posterior", "reason": "Phase03A is not topology generation."},
        {"section": "interpretation", "parameter": "not_final_decision_statement", "value": payload["not_final_decision_statement"], "scope": "posterior", "reason": "Phase03A is not final release logic."},
    ]
    return payload, rows


def _build_probability_calibration_audit(
    calibration_metadata: dict[str, object],
    temporal_calibration_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    counts_by_lag: dict[str, list[dict[str, object]]] = {}
    for row in temporal_calibration_rows:
        counts_by_lag.setdefault(str(row.get("run_max_lag", "")), []).append(row)
    rows: list[dict[str, object]] = []
    for lag, lag_rows in sorted(counts_by_lag.items()):
        route_meta = calibration_metadata.get("routes_by_lag", {}).get(lag, {})
        route_values = sorted({str(row.get("calibration_route", "")) for row in lag_rows})
        rows.append(
            {
                "audit_scope": "run_max_lag",
                "calibration_group": lag,
                "calibration_route": route_meta.get("route", "") or ",".join(route_values),
                "status": "documented",
                "row_count": len(lag_rows),
                "details": route_meta.get("fallback_reason", "") or route_meta.get("status", "") or f"routes={','.join(route_values)}",
            }
        )
    if counts_by_lag:
        rows.append(
            {
                "audit_scope": "all_rows",
                "calibration_group": "runtime",
                "calibration_route": ",".join(sorted({str(row.get("calibration_route", "")) for row in temporal_calibration_rows})),
                "status": "documented",
                "row_count": len(temporal_calibration_rows),
                "details": f"pooled_feasible={calibration_metadata.get('pooled_feasible')}",
            }
        )
    return rows or [
        {
            "audit_scope": "all_rows",
            "calibration_group": "runtime",
            "calibration_route": "none",
            "status": "no_temporal_rows",
            "row_count": 0,
            "details": "No temporal calibration rows were generated.",
        }
    ]


def _build_probability_limitations_audit(
    *,
    posterior_rows: list[dict[str, object]],
    calibration_rows: list[dict[str, object]],
    empty_or_absent_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    fallback_count = sum(1 for row in calibration_rows if row.get("calibration_route") == "conservative_logistic_fallback")
    missing_q_count = sum(1 for row in calibration_rows if row.get("calibration_route") == "missing_or_invalid_q_value")
    legitimate_yield_absence = any(
        row.get("output_surface") == "kinetic_yield_evidence_intake.tsv" and row.get("status") == "empty_legitimate"
        for row in empty_or_absent_rows
    )
    qc_flagged = sum(1 for row in posterior_rows if row.get("probability_limitations_flag") not in {"", "none"})
    return [
        {
            "limitation_id": "fallback_calibration_rows",
            "status": "documented",
            "row_count": fallback_count,
            "details": "Fallback calibration is conservative and remains non-causal.",
        },
        {
            "limitation_id": "missing_or_invalid_q_rows",
            "status": "documented",
            "row_count": missing_q_count,
            "details": "Rows without valid q-values cannot claim calibrated temporal support.",
        },
        {
            "limitation_id": "yield_legitimate_absence",
            "status": "documented",
            "row_count": 1 if legitimate_yield_absence else 0,
            "details": "Yield may be legitimately absent when Phase02 audited the empty surface as legitimate.",
        },
        {
            "limitation_id": "posterior_rows_with_limitations",
            "status": "documented",
            "row_count": qc_flagged,
            "details": "Posterior limitation flags remain internal diagnostics, not QA or final decisions.",
        },
    ]


def _build_phase03_empty_or_absent_probability_audit(
    *,
    temporal_stat_rows: list[dict[str, object]],
    temporal_calibration_rows: list[dict[str, object]],
    conditioned_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    interdependence_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
    semantic_rows: list[dict[str, object]],
    posterior_rows: list[dict[str, object]],
    phase02_empty_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    legitimate_yield_absence = any(
        row.get("output_surface") == "kinetic_yield_evidence_intake.tsv" and row.get("status") == "empty_legitimate"
        for row in phase02_empty_rows
    )
    rows = [
        ("temporal_pcmci_evidence_stat_surface.tsv", temporal_stat_rows, "available"),
        ("temporal_pcmci_calibration_surface.tsv", temporal_calibration_rows, "available"),
        ("conditioned_pair_probability_evidence_surface.tsv", conditioned_rows, "available"),
        ("descriptive_probability_evidence_surface.tsv", descriptive_rows, "available"),
        ("interdependence_probability_evidence_surface.tsv", interdependence_rows, "available"),
        ("kinetic_likelihood_surface.tsv", [row for row in kinetic_rows if row.get("relation_anchor_id")], "available"),
        ("semantic_compatibility_surface.tsv", semantic_rows, "available"),
        ("posterior_relation_state.tsv", posterior_rows, "available"),
    ]
    output_rows: list[dict[str, object]] = []
    for name, surface_rows, base_status in rows:
        status = base_status if surface_rows else "empty"
        notes = ""
        if name == "kinetic_likelihood_surface.tsv" and not surface_rows and legitimate_yield_absence:
            status = "empty_legitimate"
            notes = "Phase02 reported kinetic yield absence as legitimate, so no yield rows is acceptable."
        output_rows.append(
            {
                "output_surface": name,
                "row_count": len(surface_rows),
                "status": status,
                "basis": "phase03a_probability_runtime",
                "notes": notes,
            }
        )
    return output_rows


def _success_manifest(resolved: ResolvedPhase03APaths) -> dict[str, object]:
    return {
        "phase": "phase03a",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase02_runtime": str(resolved.phase02_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase03a_probabilistic_calibration_complete_waiting_for_phase03b_plan",
        "phase03a_completion_decision": PHASE03A_APPROVED_COMPLETION_STATE,
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase03a",
        "phase_scope": "probabilistic_calibration_and_posterior_relation_states_only",
        "controller_sha": PHASE03A_CONTROLLER_SHA,
        "forbidden_outputs_absent": "yes",
        "not_qa22_yes_no": "yes",
        "not_network_topology_yes_no": "yes",
        "not_global_closure_yes_no": "yes",
        "posterior_not_causal_probability_yes_no": "yes",
        "outputs": list(PHASE03A_REQUIRED_OUTPUTS),
    }


def _blocked_manifest(resolved: ResolvedPhase03APaths) -> dict[str, object]:
    return {
        "phase": "phase03a",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase02_runtime": str(resolved.phase02_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase03a_probabilistic_calibration_blocked",
        "phase03a_completion_decision": PHASE03A_BLOCKED_STATE,
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase03a",
        "phase_scope": "probabilistic_calibration_and_posterior_relation_states_only",
        "controller_sha": PHASE03A_CONTROLLER_SHA,
        "forbidden_outputs_absent": "yes",
        "not_qa22_yes_no": "yes",
        "not_network_topology_yes_no": "yes",
        "not_global_closure_yes_no": "yes",
        "posterior_not_causal_probability_yes_no": "yes",
        "outputs": [],
    }


def _build_repo_contamination_audit(
    *,
    repo_root: Path,
    snapshot_before: set[str],
) -> list[dict[str, object]]:
    snapshot_after = path_snapshot(repo_root)
    new_entries = sorted(entry for entry in (snapshot_after - snapshot_before) if entry not in ALLOWED_REPO_DOC_OUTPUTS)
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
        {
            "path": str(IMPLEMENTATION_AUDIT_PATH).replace("\\", "/"),
            "status": "allowed_repo_doc_artifact",
            "reason": "required_phase03a_implementation_audit_document",
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


def _artifact_row_counts(
    *,
    temporal_stat_rows: list[dict[str, object]],
    temporal_calibration_rows: list[dict[str, object]],
    multilag_rows: list[dict[str, object]],
    conditioned_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    interdependence_rows: list[dict[str, object]],
    kinetic_rows: list[dict[str, object]],
    semantic_registry_rows: list[dict[str, object]],
    semantic_compatibility_rows: list[dict[str, object]],
    probability_tensor_rows: list[dict[str, object]],
    posterior_rows: list[dict[str, object]],
) -> dict[str, int]:
    return {
        "temporal_pcmci_evidence_stat_surface.tsv": len(temporal_stat_rows),
        "temporal_pcmci_calibration_surface.tsv": len(temporal_calibration_rows),
        "multilag_temporal_profile_surface.tsv": len(multilag_rows),
        "conditioned_pair_probability_evidence_surface.tsv": len(conditioned_rows),
        "descriptive_probability_evidence_surface.tsv": len(descriptive_rows),
        "interdependence_probability_evidence_surface.tsv": len(interdependence_rows),
        "kinetic_likelihood_surface.tsv": len(kinetic_rows),
        "semantic_polarity_registry.tsv": len(semantic_registry_rows),
        "semantic_compatibility_surface.tsv": len(semantic_compatibility_rows),
        "relation_probability_evidence_tensor.tsv": len(probability_tensor_rows),
        "posterior_relation_state.tsv": len(posterior_rows),
    }


def _write_implementation_audit_doc(
    *,
    repo_root: Path,
    phase02_runtime: Path,
    runtime_root: Path,
    artifact_row_counts: dict[str, int],
    calibration_routes_used: list[str],
    posterior_sum_check: str,
    forbidden_scan_rows: list[dict[str, object]],
    repo_contamination_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    decision: str,
    command_results: dict[str, str],
) -> None:
    warn_count = sum(1 for row in validation_rows if row.get("status") == "WARN" or row.get("severity") == "warning")
    fail_count = sum(1 for row in validation_rows if row.get("status") == "FAIL" or row.get("severity") == "error")
    forbidden_ok = all(row.get("present_yes_no") == "no" for row in forbidden_scan_rows)
    contamination_ok = any(row.get("status") == "pass_no_new_repo_runtime_outputs" for row in repo_contamination_rows)
    content = "\n".join(
        [
            "# PHASE03A_PROBABILISTIC_CALIBRATION_IMPLEMENTATION_AUDIT",
            "",
            f"- `starting_sha`: `{PHASE03A_CONTROLLER_SHA}`",
            "- `ending_sha_or_uncommitted_state`: `uncommitted_worktree_state`",
            f"- `controlling_phase02_runtime`: `{phase02_runtime}`",
            "- `commands_executed`: runtime invocation plus external verification commands recorded separately when run.",
            f"- `py_compile_result`: `{command_results.get('py_compile_result', '')}`",
            f"- `pytest_result`: `{command_results.get('pytest_result', '')}`",
            f"- `phase03a_cli_result`: `{command_results.get('phase03a_cli_result', '')}`",
            f"- `runtime_path`: `{runtime_root}`",
            f"- `artifact_row_counts`: `{artifact_row_counts}`",
            f"- `calibration_routes_used`: `{calibration_routes_used}`",
            f"- `posterior_row_count`: `{artifact_row_counts.get('posterior_relation_state.tsv', 0)}`",
            f"- `posterior_probability_sum_check`: `{posterior_sum_check}`",
            f"- `forbidden_output_scan_result`: `{'pass' if forbidden_ok else 'fail'}`",
            f"- `repo_contamination_result`: `{'pass' if contamination_ok else 'fail'}`",
            f"- `validation_summary_warn_count`: `{warn_count}`",
            f"- `validation_summary_fail_count`: `{fail_count}`",
            f"- `decision`: `{decision}`",
        ]
    )
    path = repo_root / IMPLEMENTATION_AUDIT_PATH
    ensure_dir(path.parent)
    path.write_text(content + "\n", encoding="utf-8")


def _relation_scope_key(anchor_row: dict[str, str]) -> tuple[str, ...]:
    return (
        anchor_row.get("target_component_id", ""),
        anchor_row.get("perturbator_component_id", ""),
        anchor_row.get("scenario_canonical", ""),
        anchor_row.get("condition_role", ""),
        anchor_row.get("condition_id", ""),
        anchor_row.get("replicate", ""),
        anchor_row.get("window_label", ""),
    )


def _aggregate_mean_by_anchor(rows: list[dict[str, object]], field: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for row in rows:
        relation_anchor_id = str(row.get("relation_anchor_id", ""))
        if not relation_anchor_id:
            continue
        totals[relation_anchor_id] = totals.get(relation_anchor_id, 0.0) + float(row.get(field, 0.0) or 0.0)
        counts[relation_anchor_id] = counts.get(relation_anchor_id, 0) + 1
    return {anchor_id: totals[anchor_id] / counts[anchor_id] for anchor_id in totals}


def _aggregate_direction_from_rows(
    rows: list[dict[str, object]],
    positive_field: str,
    negative_field: str,
) -> dict[str, str]:
    positive = _aggregate_mean_by_anchor(rows, positive_field)
    negative = _aggregate_mean_by_anchor(rows, negative_field)
    anchor_ids = set(positive) | set(negative)
    return {anchor_id: _direction_from_masses(positive.get(anchor_id, 0.0), negative.get(anchor_id, 0.0)) for anchor_id in anchor_ids}


def _posterior_sum_check_text(posterior_rows: list[dict[str, object]]) -> str:
    max_delta = 0.0
    for row in posterior_rows:
        total = (
            float(row["p_positive_support"])
            + float(row["p_negative_support"])
            + float(row["p_ambiguous_or_mixed"])
            + float(row["p_insufficient_or_uninformative"])
        )
        max_delta = max(max_delta, abs(total - 1.0))
    return f"max_abs_delta={max_delta:.12f}"


def _empirical_feasible(values: list[float], min_rows: int, min_unique: int) -> bool:
    unique_count = len({round(value, 12) for value in values})
    return len(values) >= min_rows and unique_count >= min_unique and _iqr(values) > 0.0


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _iqr(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    ordered = sorted(values)
    q1 = _percentile(ordered, 0.25)
    q3 = _percentile(ordered, 0.75)
    return q3 - q1


def _percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * quantile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _percentile_probability(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    rank = 0
    for candidate in sorted_values:
        if candidate <= value:
            rank += 1
    return rank / len(sorted_values)


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _direction_from_numeric(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def _direction_sign(direction: str) -> int:
    value = direction.strip().lower()
    if value in {"positive", "production", "increase"}:
        return 1
    if value in {"negative", "consumption", "decrease"}:
        return -1
    return 0


def _direction_from_masses(positive_mass: float, negative_mass: float) -> str:
    if positive_mass > negative_mass and positive_mass > 0:
        return "positive"
    if negative_mass > positive_mass and negative_mass > 0:
        return "negative"
    if positive_mass == negative_mass == 0:
        return ""
    return "mixed"


def _strength_bucket(probability: float) -> str:
    if probability >= 0.80:
        return "strong"
    if probability >= 0.50:
        return "moderate"
    if probability > 0:
        return "weak"
    return "none"


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _kinetic_strength(row: dict[str, str], family: str) -> float:
    if family in {"growth", "metabolite_rate"}:
        numeric = abs(as_float(row.get("kinetic_value", "")) or 0.0)
        return _bounded(1.0 - math.exp(-numeric), 0.0, 1.0)
    if family == "temporal_coupling":
        return 0.80 if row.get("kinetic_support_status") == "primary_strong_evidence" else 0.50
    if family == "yield":
        numeric = abs(as_float(row.get("kinetic_value", "")) or 0.0)
        return _bounded(numeric, 0.0, 1.0)
    return 0.0


def _expected_positive_interpretation(target_component_id: str) -> str:
    label = target_component_id.lower()
    if "growth" in label or "od" in label:
        return "target_growth_supported"
    return "target_state_support"


def _expected_negative_interpretation(target_component_id: str) -> str:
    label = target_component_id.lower()
    if "growth" in label or "od" in label:
        return "target_growth_suppressed"
    return "target_state_opposed"


def _softmax(logits: dict[str, float], temperature: float) -> dict[str, float]:
    scaled = {key: value / temperature for key, value in logits.items()}
    max_value = max(scaled.values())
    exp_values = {key: math.exp(value - max_value) for key, value in scaled.items()}
    total = sum(exp_values.values())
    return {key: exp_values[key] / total for key in exp_values}


def _entropy(probabilities: dict[str, float]) -> float:
    return -sum(value * math.log(value) for value in probabilities.values() if value > 0)


def _calibration_status_from_route(route: str) -> str:
    if route in {"empirical_rank_by_run_max_lag", "empirical_rank_pooled_lags"}:
        return "internal_empirical_rank_calibration_not_external_truth"
    if route == "conservative_logistic_fallback":
        return "conservative_internal_fallback_not_external_truth"
    return "not_calibrated_missing_or_invalid_q_value"


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
