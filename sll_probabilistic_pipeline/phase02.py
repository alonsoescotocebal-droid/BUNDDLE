"""Phase 02 relation evidence intake runtime."""

from __future__ import annotations

from pathlib import Path

from .config import (
    PHASE02_APPROVED_COMPLETION_STATE,
    PHASE02_BLOCKED_STATE,
    PHASE02_CONTROLLER_SHA,
    PHASE02_REQUIRED_INPUTS,
    PHASE02_REQUIRED_OUTPUTS,
)
from .paths import ResolvedPhase02Paths, resolve_phase02_paths
from .utils import (
    as_float,
    ensure_dir,
    fieldnames_from_rows,
    path_snapshot,
    read_json,
    read_tsv,
    stable_trace_id,
    unique_by,
    utc_now_iso,
    write_json,
    write_tsv,
)
from .validation.phase02 import build_phase02_forbidden_scan_rows, build_phase02_validation_summary


DESCRIPTIVE_NATURAL_KEY = (
    "condition_id",
    "scenario_canonical",
    "condition_role",
    "replicate",
    "canonical_component_id",
    "descriptive_measure_type",
    "timepoint_label",
    "window_label",
)


def run_phase02(
    *,
    repo_root: str | Path,
    phase01b_runtime: str | Path,
    out_root: str | Path,
    strict: bool,
) -> dict[str, object]:
    repo_snapshot_before = path_snapshot(Path(repo_root).resolve(strict=False))
    resolved = resolve_phase02_paths(
        repo_root=repo_root,
        phase01b_runtime=phase01b_runtime,
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
            "notes": "Phase 02 runtime created under allowed external results root.",
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
    input_surface_manifest_rows = _build_input_surface_manifest(resolved.phase01b_runtime)
    preflight_rows = _build_preflight_audit(
        resolved=resolved,
        input_manifest=input_manifest,
        input_validation_rows=input_validation_rows,
        input_surface_manifest_rows=input_surface_manifest_rows,
    )
    _write_table(
        data_dir / "phase02_input_runtime_manifest_audit.tsv",
        input_manifest_audit_rows,
        preferred_order=list(input_manifest_audit_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase02_input_surface_manifest.tsv",
        input_surface_manifest_rows,
        preferred_order=list(input_surface_manifest_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase02_preflight_audit.tsv",
        preflight_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )

    preflight_failed = any(row.get("status") == "FAIL" for row in preflight_rows)
    repo_contamination_rows = _build_repo_contamination_audit(
        repo_root=resolved.repo_root,
        snapshot_before=repo_snapshot_before,
    )
    _write_table(
        audit_dir / "repo_contamination_audit.tsv",
        repo_contamination_rows,
        preferred_order=list(repo_contamination_rows[0].keys()),
    )

    if preflight_failed:
        forbidden_scan_rows = build_phase02_forbidden_scan_rows(runtime_root)
        _write_table(
            data_dir / "phase02_forbidden_output_scan.tsv",
            forbidden_scan_rows,
            preferred_order=list(forbidden_scan_rows[0].keys()),
        )
        empty_rows = [
            {
                "output_surface": "phase02_runtime",
                "row_count": "",
                "status": "blocked_preflight_failure",
                "basis": "phase02_preflight",
                "notes": "Phase 02 stopped before evidence surface construction.",
            }
        ]
        _write_table(
            data_dir / "phase02_empty_or_absent_evidence_audit.tsv",
            empty_rows,
            preferred_order=list(empty_rows[0].keys()),
        )
        manifest = _blocked_manifest(resolved)
        write_json(manifest_dir / "runtime_manifest.json", manifest)
        validation_rows = build_phase02_validation_summary(
            runtime_root=runtime_root,
            required_outputs=(
                "manifest/runtime_manifest.json",
                "data/phase02_input_runtime_manifest_audit.tsv",
                "data/phase02_input_surface_manifest.tsv",
                "data/phase02_preflight_audit.tsv",
                "data/phase02_forbidden_output_scan.tsv",
                "data/phase02_empty_or_absent_evidence_audit.tsv",
                "audit/output_root_boundary_audit.tsv",
                "audit/repo_contamination_audit.tsv",
                "audit/phase02_validation_summary.tsv",
            ),
            output_root_boundary_rows=output_root_boundary_rows,
            repo_contamination_rows=repo_contamination_rows,
            manifest=manifest,
            preflight_rows=preflight_rows,
            join_contract_audit_rows=[],
            anchor_rows=[],
            tensor_rows=[],
            tensor_fieldnames=[],
            forbidden_scan_rows=forbidden_scan_rows,
            kinetic_rows=[],
            empty_or_absent_rows=empty_rows,
        )
        _write_table(
            audit_dir / "phase02_validation_summary.tsv",
            validation_rows,
            preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
        )
        return manifest

    inputs = _load_phase01b_inputs(resolved.phase01b_runtime)
    join_admissibility_index = _build_join_admissibility_index(inputs["join_admissibility_contract.tsv"])
    growth_policy_components = _build_growth_policy_components(inputs["growth_variable_identity_audit.tsv"])

    anchor_rows = _build_relation_anchor_registry(inputs["stat_pcmci_edge_long.tsv"])
    component_context_index = _build_anchor_component_index(anchor_rows)
    pair_context_index = _build_anchor_pair_context_index(anchor_rows)
    conditioned_pair_index = _build_anchor_conditioned_pair_index(anchor_rows)

    temporal_rows = _build_temporal_evidence_rows(inputs["stat_pcmci_edge_long.tsv"], anchor_rows)
    descriptive_rows = _build_descriptive_evidence_rows(
        inputs["stat_descriptive_node_state_long.tsv"],
        component_context_index,
        join_admissibility_index,
    )
    interdependence_rows = _build_interdependence_evidence_rows(
        inputs["stat_interdependence_pair_window_long.tsv"],
        pair_context_index,
    )
    conditioned_rows = _build_conditioned_pair_evidence_rows(
        inputs["stat_conditioned_pair_global_long.tsv"],
        conditioned_pair_index,
    )
    growth_rows = _build_kinetic_growth_rows(
        inputs["kinetic_growth_primary_long.tsv"],
        component_context_index,
        growth_policy_components,
    )
    rate_rows = _build_kinetic_rate_rows(
        inputs["kinetic_rate_primary_long.tsv"],
        component_context_index,
    )
    coupling_rows = _build_kinetic_temporal_coupling_rows(
        inputs["kinetic_temporal_coupling_primary_long.tsv"],
        component_context_index,
    )
    yield_rows = _build_kinetic_yield_rows(
        inputs["kinetic_yield_primary_long.tsv"],
        component_context_index,
    )
    join_contract_audit_rows = _build_phase02_join_contract_consumption_audit(
        contract_rows=inputs["phase02_join_contract.tsv"],
        join_admissibility_rows=inputs["join_admissibility_contract.tsv"],
        descriptive_rows=descriptive_rows,
        growth_rows=growth_rows,
    )
    tensor_rows = _build_relation_evidence_tensor(
        anchor_rows=anchor_rows,
        temporal_rows=temporal_rows,
        descriptive_rows=descriptive_rows,
        interdependence_rows=interdependence_rows,
        conditioned_rows=conditioned_rows,
        growth_rows=growth_rows,
        rate_rows=rate_rows,
        coupling_rows=coupling_rows,
        yield_rows=yield_rows,
    )
    empty_or_absent_rows = _build_empty_or_absent_evidence_audit(
        temporal_rows=temporal_rows,
        descriptive_rows=descriptive_rows,
        interdependence_rows=interdependence_rows,
        conditioned_rows=conditioned_rows,
        growth_rows=growth_rows,
        rate_rows=rate_rows,
        coupling_rows=coupling_rows,
        yield_rows=yield_rows,
        input_yield_rows=inputs["kinetic_yield_primary_long.tsv"],
    )

    _write_table(
        data_dir / "relation_anchor_registry.tsv",
        anchor_rows,
        preferred_order=[
            "relation_anchor_id",
            "anchor_scope",
            "target_component_id",
            "perturbator_component_id",
            "scenario_canonical",
            "condition_role",
            "condition_id",
            "replicate",
            "window_label",
            "run_max_lag",
            "edge_lag",
            "source_surfaces",
            "anchor_origin",
            "join_contract_role",
            "direct_read_yes_no",
            "inference_used_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "stat_temporal_pcmci_evidence_intake.tsv",
        temporal_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "run_max_lag",
            "edge_lag",
            "source_component_id",
            "target_component_id",
            "effect_sign",
            "effect_value",
            "p_value",
            "q_value",
            "temporal_evidence_stat",
            "not_probability_yes_no",
            "direct_read_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "stat_descriptive_evidence_intake.tsv",
        descriptive_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "canonical_component_id",
            "scenario_canonical",
            "condition_role",
            "condition_id",
            "replicate",
            "window_label",
            "descriptive_measure_type",
            "descriptive_value",
            "descriptive_direction",
            "projection_role",
            "join_admissibility",
            "direct_read_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "stat_interdependence_evidence_intake.tsv",
        interdependence_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "left_component_id",
            "right_component_id",
            "scenario_canonical",
            "condition_role",
            "condition_id",
            "replicate",
            "window_label",
            "interdependence_measure",
            "interdependence_value",
            "pair_role",
            "direct_read_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "stat_conditioned_pair_evidence_intake.tsv",
        conditioned_rows,
        preferred_order=[
            "relation_anchor_id",
            "source_surface",
            "source_row_key",
            "left_component_id",
            "right_component_id",
            "conditioned_measure",
            "conditioned_value",
            "conditioned_sign",
            "direction_allowed_yes_no",
            "direct_read_yes_no",
            "trace_id",
        ],
    )
    _write_table(
        data_dir / "kinetic_growth_evidence_intake.tsv",
        growth_rows,
        preferred_order=_preferred_kinetic_output_order(),
    )
    _write_table(
        data_dir / "kinetic_rate_evidence_intake.tsv",
        rate_rows,
        preferred_order=_preferred_kinetic_output_order(),
    )
    _write_table(
        data_dir / "kinetic_temporal_coupling_evidence_intake.tsv",
        coupling_rows,
        preferred_order=_preferred_kinetic_output_order(),
    )
    _write_table(
        data_dir / "kinetic_yield_evidence_intake.tsv",
        yield_rows,
        preferred_order=_preferred_kinetic_output_order(),
    )
    _write_table(
        data_dir / "phase02_join_contract_consumption_audit.tsv",
        join_contract_audit_rows,
        preferred_order=list(join_contract_audit_rows[0].keys()),
    )
    tensor_fieldnames = fieldnames_from_rows(
        tensor_rows,
        [
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
            "has_temporal_pcmci_evidence",
            "has_descriptive_evidence",
            "has_interdependence_evidence",
            "has_conditioned_pair_evidence",
            "has_kinetic_growth_evidence",
            "has_kinetic_rate_evidence",
            "has_kinetic_temporal_coupling_evidence",
            "has_kinetic_yield_evidence",
            "evidence_layer_count",
            "evidence_conflict_flag",
            "join_contract_role",
            "relation_intake_status",
            "not_posterior_yes_no",
            "direct_read_yes_no",
            "inference_used_yes_no",
            "trace_id",
        ],
    )
    write_tsv(data_dir / "relation_evidence_tensor.tsv", tensor_rows, tensor_fieldnames)
    forbidden_scan_rows = build_phase02_forbidden_scan_rows(runtime_root)
    _write_table(
        data_dir / "phase02_forbidden_output_scan.tsv",
        forbidden_scan_rows,
        preferred_order=list(forbidden_scan_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase02_empty_or_absent_evidence_audit.tsv",
        empty_or_absent_rows,
        preferred_order=list(empty_or_absent_rows[0].keys()),
    )

    manifest = _success_manifest(resolved)
    write_json(manifest_dir / "runtime_manifest.json", manifest)

    validation_rows = build_phase02_validation_summary(
        runtime_root=runtime_root,
        required_outputs=PHASE02_REQUIRED_OUTPUTS,
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        manifest=manifest,
        preflight_rows=preflight_rows,
        join_contract_audit_rows=join_contract_audit_rows,
        anchor_rows=anchor_rows,
        tensor_rows=tensor_rows,
        tensor_fieldnames=tensor_fieldnames,
        forbidden_scan_rows=forbidden_scan_rows,
        kinetic_rows=growth_rows + rate_rows + coupling_rows + yield_rows,
        empty_or_absent_rows=empty_or_absent_rows,
    )
    _write_table(
        audit_dir / "phase02_validation_summary.tsv",
        validation_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    return manifest


def _load_phase01b_inputs(runtime_root: Path) -> dict[str, list[dict[str, str]]]:
    table_names = (
        "growth_variable_identity_audit.tsv",
        "stat_pcmci_edge_long.tsv",
        "stat_descriptive_node_state_long.tsv",
        "stat_interdependence_pair_window_long.tsv",
        "stat_conditioned_pair_global_long.tsv",
        "kinetic_growth_primary_long.tsv",
        "kinetic_rate_primary_long.tsv",
        "kinetic_temporal_coupling_primary_long.tsv",
        "kinetic_yield_primary_long.tsv",
        "join_admissibility_contract.tsv",
        "phase02_join_contract.tsv",
    )
    return {
        name: read_tsv(runtime_root / "data" / name)
        for name in table_names
    }


def _build_input_runtime_manifest_audit(manifest: dict[str, object]) -> list[dict[str, object]]:
    expectations = {
        "phase": "phase01b",
        "phase_status": "phase01b_complete_waiting_for_phase02_approval",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase01b",
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
            "expected_value": "phase01b_runtime_path",
            "status": "PASS" if manifest.get("runtime_root") else "FAIL",
            "notes": "Phase 02 consumes the normalized Phase 01B runtime only.",
        }
    )
    return rows


def _build_input_surface_manifest(runtime_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in PHASE02_REQUIRED_INPUTS:
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


def _build_join_admissibility_index(
    join_admissibility_rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row.get("left_surface", ""), row.get("right_surface", "")): row
        for row in join_admissibility_rows
        if row.get("resolution_state") == "resolved"
    }


def _build_growth_policy_components(growth_identity_rows: list[dict[str, str]]) -> set[str]:
    components: set[str] = set()
    for row in growth_identity_rows:
        if str(row.get("can_join_to_kinetic_OD600", "")).strip().lower() == "yes":
            components.add(row.get("canonical_growth_id", ""))
    return components


def _descriptive_join_admissibility(
    join_admissibility_index: dict[tuple[str, str], dict[str, str]],
) -> str:
    values = {
        join_admissibility_index.get(
            ("stat_descriptive_node_state_long.tsv", right_surface),
            {},
        ).get("join_admissibility", "")
        for right_surface in (
            "kinetic_rate_primary_long.tsv",
            "kinetic_temporal_coupling_primary_long.tsv",
        )
    }
    values.discard("")
    if len(values) == 1:
        return next(iter(values))
    return "contract_mismatch"


def _build_preflight_audit(
    *,
    resolved: ResolvedPhase02Paths,
    input_manifest: dict[str, object],
    input_validation_rows: list[dict[str, str]],
    input_surface_manifest_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.append(
        _summary_row(
            "phase01b_runtime_exists",
            "PASS" if resolved.phase01b_runtime.exists() else "FAIL",
            "info" if resolved.phase01b_runtime.exists() else "error",
            "phase01b_runtime",
            str(resolved.phase01b_runtime),
            str(resolved.phase01b_runtime),
        )
    )

    manifest_ok = (
        input_manifest.get("phase") == "phase01b"
        and input_manifest.get("phase_status") == "phase01b_complete_waiting_for_phase02_approval"
        and input_manifest.get("pipeline_global_status") == "not_closed"
    )
    rows.append(
        _summary_row(
            "phase01b_manifest_state_valid",
            "PASS" if manifest_ok else "FAIL",
            "info" if manifest_ok else "error",
            "manifest/runtime_manifest.json",
            "phase_state",
            (
                f"phase={input_manifest.get('phase')};phase_status={input_manifest.get('phase_status')};"
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
            "phase01b_validation_clean",
            "PASS" if validation_clean else "FAIL",
            "info" if validation_clean else "error",
            "audit/phase01b_validation_summary.tsv",
            "warning_fail_counts",
            f"warning_count={warning_count};fail_count={fail_count}",
        )
    )

    missing_inputs = [row["relative_path"] for row in input_surface_manifest_rows if row.get("exists_yes_no") != "yes"]
    rows.append(
        _summary_row(
            "phase01b_required_inputs_present",
            "PASS" if not missing_inputs else "FAIL",
            "info" if not missing_inputs else "error",
            "data/phase02_input_surface_manifest.tsv",
            "required_inputs",
            "none_missing" if not missing_inputs else ";".join(missing_inputs),
        )
    )

    phase02_contract_rows = read_tsv(resolved.phase01b_runtime / "data" / "phase02_join_contract.tsv")
    phase02_contract_ok = bool(phase02_contract_rows) and all(row.get("resolution_state") == "resolved" for row in phase02_contract_rows)
    rows.append(
        _summary_row(
            "phase02_join_contract_present",
            "PASS" if phase02_contract_ok else "FAIL",
            "info" if phase02_contract_ok else "error",
            "data/phase02_join_contract.tsv",
            "resolution_state",
            f"row_count={len(phase02_contract_rows)}",
        )
    )

    join_contract_rows = read_tsv(resolved.phase01b_runtime / "data" / "join_admissibility_contract.tsv")
    join_contract_ok = bool(join_contract_rows) and all(row.get("resolution_state") == "resolved" for row in join_contract_rows)
    rows.append(
        _summary_row(
            "join_admissibility_contract_present",
            "PASS" if join_contract_ok else "FAIL",
            "info" if join_contract_ok else "error",
            "data/join_admissibility_contract.tsv",
            "resolution_state",
            f"row_count={len(join_contract_rows)}",
        )
    )

    many_to_many_ok = all(
        row.get("phase02_consumption_mode") in {
            "deduplicate_lag_invariant_descriptive_then_project_to_kinetic_component_context",
            "identity_policy_lookup_only_do_not_join_as_measurement",
        }
        and row.get("resolution_state") == "resolved"
        for row in phase02_contract_rows
    )
    rows.append(
        _summary_row(
            "many_to_many_not_reopened",
            "PASS" if many_to_many_ok else "FAIL",
            "info" if many_to_many_ok else "error",
            "data/phase02_join_contract.tsv",
            "phase02_consumption_mode",
            f"row_count={len(phase02_contract_rows)}",
        )
    )

    kinetic_tables = (
        read_tsv(resolved.phase01b_runtime / "data" / "kinetic_growth_primary_long.tsv"),
        read_tsv(resolved.phase01b_runtime / "data" / "kinetic_rate_primary_long.tsv"),
        read_tsv(resolved.phase01b_runtime / "data" / "kinetic_temporal_coupling_primary_long.tsv"),
        read_tsv(resolved.phase01b_runtime / "data" / "kinetic_yield_primary_long.tsv"),
    )
    kinetic_real_only_ok = all(row.get("branch", "real_only") == "real_only" for table in kinetic_tables for row in table)
    rows.append(
        _summary_row(
            "kinetic_real_only_only",
            "PASS" if kinetic_real_only_ok else "FAIL",
            "info" if kinetic_real_only_ok else "error",
            "data/kinetic_*_primary_long.tsv",
            "branch",
            "Phase 02 consumes only normalized real_only kinetic outputs.",
        )
    )

    rows.append(
        _summary_row(
            "no_raw_roots_consumed",
            "PASS",
            "info",
            "phase02_runtime",
            "input_boundary",
            "Phase 02 consumed only the rebuilt Phase 01B runtime outputs and did not open raw statistical or kinetic roots.",
        )
    )

    forbidden_preexisting = build_phase02_forbidden_scan_rows(resolved.phase01b_runtime)
    forbidden_preexisting_ok = all(row.get("present_yes_no") == "no" for row in forbidden_preexisting)
    rows.append(
        _summary_row(
            "no_forbidden_outputs_before_run",
            "PASS" if forbidden_preexisting_ok else "FAIL",
            "info" if forbidden_preexisting_ok else "error",
            "phase01b_runtime",
            "forbidden_outputs",
            "none_present" if forbidden_preexisting_ok else "phase02_or_later_outputs_detected_in_input_runtime",
        )
    )
    return rows


def _build_relation_anchor_registry(edge_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    anchors: list[dict[str, object]] = []
    for row in edge_rows:
        relation_anchor_id = stable_trace_id(
            "phase02_anchor",
            row.get("condition_id", ""),
            row.get("scenario_canonical", ""),
            row.get("condition_role", ""),
            row.get("replicate", ""),
            row.get("source_canonical_component_id", ""),
            row.get("target_canonical_component_id", ""),
            row.get("run_max_lag", ""),
            row.get("edge_lag", ""),
        )
        anchors.append(
            {
                "relation_anchor_id": relation_anchor_id,
                "anchor_scope": "directed_relation",
                "target_component_id": row.get("target_canonical_component_id", ""),
                "perturbator_component_id": row.get("source_canonical_component_id", ""),
                "scenario_canonical": row.get("scenario_canonical", ""),
                "condition_role": row.get("condition_role", ""),
                "condition_id": row.get("condition_id", ""),
                "replicate": row.get("replicate", ""),
                "window_label": "",
                "run_max_lag": row.get("run_max_lag", ""),
                "edge_lag": row.get("edge_lag", ""),
                "source_surfaces": "stat_pcmci_edge_long.tsv",
                "anchor_origin": "phase01b_stat_pcmci_edge_long",
                "join_contract_role": "temporal_anchor",
                "direct_read_yes_no": "no",
                "inference_used_yes_no": "yes",
                "trace_id": stable_trace_id("phase02_anchor_registry", relation_anchor_id, row.get("source_row_key", "")),
            }
        )
    return anchors


def _build_anchor_component_index(anchor_rows: list[dict[str, object]]) -> dict[tuple[str, ...], list[tuple[str, str]]]:
    index: dict[tuple[str, ...], list[tuple[str, str]]] = {}
    for row in anchor_rows:
        common = (
            str(row.get("condition_id", "")),
            str(row.get("scenario_canonical", "")),
            str(row.get("condition_role", "")),
            str(row.get("replicate", "")),
        )
        target_key = common + (str(row.get("target_component_id", "")),)
        source_key = common + (str(row.get("perturbator_component_id", "")),)
        index.setdefault(target_key, []).append((str(row.get("relation_anchor_id", "")), "target_component"))
        index.setdefault(source_key, []).append((str(row.get("relation_anchor_id", "")), "perturbator_component"))
    return index


def _build_anchor_pair_context_index(anchor_rows: list[dict[str, object]]) -> dict[tuple[str, ...], list[str]]:
    index: dict[tuple[str, ...], list[str]] = {}
    for row in anchor_rows:
        pair_key = _pair_key(str(row.get("target_component_id", "")), str(row.get("perturbator_component_id", "")))
        key = (
            str(row.get("condition_id", "")),
            str(row.get("scenario_canonical", "")),
            str(row.get("condition_role", "")),
            pair_key,
        )
        index.setdefault(key, []).append(str(row.get("relation_anchor_id", "")))
    return index


def _build_anchor_conditioned_pair_index(anchor_rows: list[dict[str, object]]) -> dict[tuple[str, ...], list[str]]:
    index: dict[tuple[str, ...], list[str]] = {}
    for row in anchor_rows:
        pair_key = _pair_key(str(row.get("target_component_id", "")), str(row.get("perturbator_component_id", "")))
        exact_key = (
            str(row.get("scenario_canonical", "")),
            str(row.get("condition_role", "")),
            pair_key,
        )
        broad_key = ("", str(row.get("condition_role", "")), pair_key)
        index.setdefault(exact_key, []).append(str(row.get("relation_anchor_id", "")))
        index.setdefault(broad_key, []).append(str(row.get("relation_anchor_id", "")))
    return index


def _build_temporal_evidence_rows(
    edge_rows: list[dict[str, str]],
    anchor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    anchor_ids = [str(row.get("relation_anchor_id", "")) for row in anchor_rows]
    rows: list[dict[str, object]] = []
    for anchor_id, row in zip(anchor_ids, edge_rows, strict=False):
        effect_value = as_float(row.get("effect"))
        rows.append(
            {
                "relation_anchor_id": anchor_id,
                "source_surface": "stat_pcmci_edge_long.tsv",
                "source_row_key": row.get("source_row_key", ""),
                "run_max_lag": row.get("run_max_lag", ""),
                "edge_lag": row.get("edge_lag", ""),
                "source_component_id": row.get("source_canonical_component_id", ""),
                "target_component_id": row.get("target_canonical_component_id", ""),
                "effect_sign": _sign_text(effect_value),
                "effect_value": row.get("effect", ""),
                "p_value": "",
                "q_value": row.get("q_value", ""),
                "temporal_evidence_stat": row.get("effect", ""),
                "not_probability_yes_no": "yes",
                "direct_read_yes_no": "yes",
                "trace_id": stable_trace_id("phase02_temporal", anchor_id, row.get("source_row_key", "")),
            }
        )
    return rows


def _build_descriptive_evidence_rows(
    descriptive_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
    join_admissibility_index: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    deduplicated = unique_by(descriptive_rows, DESCRIPTIVE_NATURAL_KEY)
    descriptive_join_admissibility = _descriptive_join_admissibility(join_admissibility_index)
    rows: list[dict[str, object]] = []
    for row in deduplicated:
        key = (
            row.get("condition_id", ""),
            row.get("scenario_canonical", ""),
            row.get("condition_role", ""),
            row.get("replicate", ""),
            row.get("canonical_component_id", ""),
        )
        for relation_anchor_id, projection_role in component_context_index.get(key, []):
            value = as_float(row.get("metric_value"))
            rows.append(
                {
                    "relation_anchor_id": relation_anchor_id,
                    "source_surface": "stat_descriptive_node_state_long.tsv",
                    "source_row_key": row.get("source_row_key", ""),
                    "canonical_component_id": row.get("canonical_component_id", ""),
                    "scenario_canonical": row.get("scenario_canonical", ""),
                    "condition_role": row.get("condition_role", ""),
                    "condition_id": row.get("condition_id", ""),
                    "replicate": row.get("replicate", ""),
                    "window_label": row.get("window_label") or row.get("timepoint_label", ""),
                    "descriptive_measure_type": row.get("descriptive_measure_type", ""),
                    "descriptive_value": row.get("metric_value", ""),
                    "descriptive_direction": _sign_text(value),
                    "projection_role": projection_role,
                    "join_admissibility": descriptive_join_admissibility,
                    "direct_read_yes_no": "yes",
                    "trace_id": stable_trace_id("phase02_descriptive", relation_anchor_id, row.get("source_row_key", ""), projection_role),
                }
            )
    return rows


def _build_interdependence_evidence_rows(
    interdependence_rows: list[dict[str, str]],
    pair_context_index: dict[tuple[str, ...], list[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in interdependence_rows:
        pair_key = _pair_key(row.get("variable_i_canonical_component_id", ""), row.get("variable_j_canonical_component_id", ""))
        key = (
            row.get("condition_id", ""),
            row.get("scenario_canonical", ""),
            row.get("condition_role", ""),
            pair_key,
        )
        for relation_anchor_id in pair_context_index.get(key, []):
            rows.append(
                {
                    "relation_anchor_id": relation_anchor_id,
                    "source_surface": "stat_interdependence_pair_window_long.tsv",
                    "source_row_key": row.get("source_row_key", ""),
                    "left_component_id": row.get("variable_i_canonical_component_id", ""),
                    "right_component_id": row.get("variable_j_canonical_component_id", ""),
                    "scenario_canonical": row.get("scenario_canonical", ""),
                    "condition_role": row.get("condition_role", ""),
                    "condition_id": row.get("condition_id", ""),
                    "replicate": "",
                    "window_label": row.get("window", ""),
                    "interdependence_measure": row.get("relationship_label") or row.get("value_type", ""),
                    "interdependence_value": f"{row.get('delta_i_mean', '')}|{row.get('delta_j_mean', '')}",
                    "pair_role": "undirected_pair_projected",
                    "direct_read_yes_no": "yes",
                    "trace_id": stable_trace_id("phase02_interdependence", relation_anchor_id, row.get("source_row_key", "")),
                }
            )
    return rows


def _build_conditioned_pair_evidence_rows(
    conditioned_rows: list[dict[str, str]],
    conditioned_pair_index: dict[tuple[str, ...], list[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in conditioned_rows:
        pair_key = _pair_key(row.get("variable_i_canonical_component_id", ""), row.get("variable_j_canonical_component_id", ""))
        key = (
            row.get("scenario_canonical", ""),
            row.get("condition_role", ""),
            pair_key,
        )
        for relation_anchor_id in conditioned_pair_index.get(key, []):
            rows.append(
                {
                    "relation_anchor_id": relation_anchor_id,
                    "source_surface": "stat_conditioned_pair_global_long.tsv",
                    "source_row_key": row.get("source_row_key", ""),
                    "left_component_id": row.get("variable_i_canonical_component_id", ""),
                    "right_component_id": row.get("variable_j_canonical_component_id", ""),
                    "conditioned_measure": row.get("value_type") or "partialcorr",
                    "conditioned_value": row.get("partialcorr", ""),
                    "conditioned_sign": row.get("sign", ""),
                    "direction_allowed_yes_no": "no",
                    "direct_read_yes_no": "yes",
                    "trace_id": stable_trace_id("phase02_conditioned", relation_anchor_id, row.get("source_row_key", "")),
                }
            )
    return rows


def _build_kinetic_growth_rows(
    growth_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
    growth_policy_components: set[str],
) -> list[dict[str, object]]:
    rows = _build_component_projected_kinetic_rows(
        source_rows=[
            row
            for row in growth_rows
            if row.get("canonical_component_id", "") in growth_policy_components
        ],
        component_context_index=component_context_index,
        source_surface="kinetic_growth_primary_long.tsv",
        measure_field="mu_h_inv",
        measure_type="mu_h_inv",
        direction_field="mu_h_inv",
        role_prefix="growth",
        status_field="allowed_for_primary_handoff",
        window_fields=("t_start", "t_end"),
    )
    for row in rows:
        row["kinetic_role"] = f"{row.get('kinetic_role', '')}_policy_lookup_only"
    return rows


def _build_kinetic_rate_rows(
    rate_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
) -> list[dict[str, object]]:
    return _build_component_projected_kinetic_rows(
        source_rows=rate_rows,
        component_context_index=component_context_index,
        source_surface="kinetic_rate_primary_long.tsv",
        measure_field="slope_volumetric_per_h",
        measure_type="slope_volumetric_per_h",
        direction_field="direction",
        role_prefix="rate",
        status_field="final_usage_decision",
        window_fields=("t_start", "t_end"),
    )


def _build_kinetic_temporal_coupling_rows(
    coupling_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
) -> list[dict[str, object]]:
    return _build_component_projected_kinetic_rows(
        source_rows=coupling_rows,
        component_context_index=component_context_index,
        source_surface="kinetic_temporal_coupling_primary_long.tsv",
        measure_field="temporal_classification",
        measure_type="temporal_classification",
        direction_field="rate_direction",
        role_prefix="temporal_coupling",
        status_field="final_usage_decision",
        window_fields=("growth_t_start", "rate_t_end"),
    )


def _build_kinetic_yield_rows(
    yield_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
) -> list[dict[str, object]]:
    return _build_component_projected_kinetic_rows(
        source_rows=yield_rows,
        component_context_index=component_context_index,
        source_surface="kinetic_yield_primary_long.tsv",
        measure_field="yield_value",
        measure_type="yield_value",
        direction_field="yield_direction",
        role_prefix="yield",
        status_field="allowed_for_primary_handoff",
        window_fields=("t_start", "t_end"),
    )


def _build_component_projected_kinetic_rows(
    *,
    source_rows: list[dict[str, str]],
    component_context_index: dict[tuple[str, ...], list[tuple[str, str]]],
    source_surface: str,
    measure_field: str,
    measure_type: str,
    direction_field: str,
    role_prefix: str,
    status_field: str,
    window_fields: tuple[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in source_rows:
        key = (
            row.get("condition_id", ""),
            row.get("scenario_canonical", ""),
            row.get("condition_role", ""),
            row.get("replicate", ""),
            row.get("canonical_component_id", ""),
        )
        for relation_anchor_id, projection_role in component_context_index.get(key, []):
            rows.append(
                {
                    "relation_anchor_id": relation_anchor_id,
                    "source_surface": source_surface,
                    "source_row_key": row.get("source_row_key", ""),
                    "branch": row.get("branch", ""),
                    "canonical_component_id": row.get("canonical_component_id", ""),
                    "scenario_canonical": row.get("scenario_canonical", ""),
                    "condition_role": row.get("condition_role", ""),
                    "condition_id": row.get("condition_id", ""),
                    "replicate": row.get("replicate", ""),
                    "time_window_or_interval": _window_text(row, *window_fields),
                    "kinetic_measure_type": measure_type,
                    "kinetic_value": row.get(measure_field, ""),
                    "kinetic_direction": _direction_text(row.get(direction_field, "")),
                    "kinetic_role": f"{role_prefix}_{projection_role}",
                    "kinetic_support_status": row.get(status_field, ""),
                    "direct_read_yes_no": "yes",
                    "trace_id": stable_trace_id("phase02_kinetic", source_surface, relation_anchor_id, row.get("source_row_key", ""), projection_role),
                }
            )
    return rows


def _build_phase02_join_contract_consumption_audit(
    *,
    contract_rows: list[dict[str, str]],
    join_admissibility_rows: list[dict[str, str]],
    descriptive_rows: list[dict[str, object]],
    growth_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    join_admissibility_index = {
        (row.get("left_surface", ""), row.get("right_surface", "")): row
        for row in join_admissibility_rows
    }
    rows: list[dict[str, object]] = []
    for row in contract_rows:
        contract_key = (row.get("left_surface", ""), row.get("right_surface", ""))
        admissibility_row = join_admissibility_index.get(contract_key, {})
        if row.get("phase02_consumption_mode") == "identity_policy_lookup_only_do_not_join_as_measurement":
            output_surface = "kinetic_growth_evidence_intake.tsv"
            consumed_count = len(growth_rows)
            expected_admissibility = "policy_lookup_only"
        else:
            output_surface = "stat_descriptive_evidence_intake.tsv"
            consumed_count = len(descriptive_rows)
            expected_admissibility = "projection_only"
        actual_status = (
            "pass"
            if row.get("resolution_state") == "resolved"
            and admissibility_row.get("resolution_state") == "resolved"
            and admissibility_row.get("join_admissibility") == expected_admissibility
            and consumed_count > 0
            else "fail"
        )
        rows.append(
            {
                "left_surface": row.get("left_surface", ""),
                "right_surface": row.get("right_surface", ""),
                "phase02_consumption_mode": row.get("phase02_consumption_mode", ""),
                "join_admissibility": admissibility_row.get("join_admissibility", ""),
                "surface_usage_class": admissibility_row.get("surface_usage_class", ""),
                "contract_resolution_state": row.get("resolution_state", ""),
                "admissibility_resolution_state": admissibility_row.get("resolution_state", ""),
                "consumed_output_surface": output_surface,
                "consumed_row_count": consumed_count,
                "actual_consumption_status": actual_status,
                "details": row.get("notes", "") or admissibility_row.get("notes", ""),
            }
        )
    return rows


def _build_relation_evidence_tensor(
    *,
    anchor_rows: list[dict[str, object]],
    temporal_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    interdependence_rows: list[dict[str, object]],
    conditioned_rows: list[dict[str, object]],
    growth_rows: list[dict[str, object]],
    rate_rows: list[dict[str, object]],
    coupling_rows: list[dict[str, object]],
    yield_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    index = {str(row.get("relation_anchor_id", "")): row for row in anchor_rows}
    flags = {
        "has_temporal_pcmci_evidence": _flag_index(temporal_rows),
        "has_descriptive_evidence": _flag_index(descriptive_rows),
        "has_interdependence_evidence": _flag_index(interdependence_rows),
        "has_conditioned_pair_evidence": _flag_index(conditioned_rows),
        "has_kinetic_growth_evidence": _flag_index(growth_rows),
        "has_kinetic_rate_evidence": _flag_index(rate_rows),
        "has_kinetic_temporal_coupling_evidence": _flag_index(coupling_rows),
        "has_kinetic_yield_evidence": _flag_index(yield_rows),
    }
    rows: list[dict[str, object]] = []
    for relation_anchor_id, anchor in index.items():
        row = {
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
            "join_contract_role": anchor.get("join_contract_role", ""),
            "not_posterior_yes_no": "yes",
            "direct_read_yes_no": "no",
            "inference_used_yes_no": "yes",
            "trace_id": stable_trace_id("phase02_tensor", relation_anchor_id),
        }
        count = 0
        for field, field_index in flags.items():
            present = relation_anchor_id in field_index
            row[field] = "yes" if present else "no"
            if present:
                count += 1
        row["evidence_layer_count"] = count
        row["evidence_conflict_flag"] = "no"
        row["relation_intake_status"] = "relation_evidence_intake_complete" if count > 0 else "anchor_without_projected_support"
        rows.append(row)
    return rows


def _build_empty_or_absent_evidence_audit(
    *,
    temporal_rows: list[dict[str, object]],
    descriptive_rows: list[dict[str, object]],
    interdependence_rows: list[dict[str, object]],
    conditioned_rows: list[dict[str, object]],
    growth_rows: list[dict[str, object]],
    rate_rows: list[dict[str, object]],
    coupling_rows: list[dict[str, object]],
    yield_rows: list[dict[str, object]],
    input_yield_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    surfaces = [
        ("stat_temporal_pcmci_evidence_intake.tsv", temporal_rows),
        ("stat_descriptive_evidence_intake.tsv", descriptive_rows),
        ("stat_interdependence_evidence_intake.tsv", interdependence_rows),
        ("stat_conditioned_pair_evidence_intake.tsv", conditioned_rows),
        ("kinetic_growth_evidence_intake.tsv", growth_rows),
        ("kinetic_rate_evidence_intake.tsv", rate_rows),
        ("kinetic_temporal_coupling_evidence_intake.tsv", coupling_rows),
        ("kinetic_yield_evidence_intake.tsv", yield_rows),
    ]
    rows: list[dict[str, object]] = []
    for name, surface_rows in surfaces:
        if name == "kinetic_yield_evidence_intake.tsv" and not input_yield_rows:
            status = "empty_legitimate"
            notes = "Input kinetic_yield_primary_long.tsv is header-only or empty and is accepted as legitimate absence."
        else:
            status = "available" if surface_rows else "empty"
            notes = ""
        rows.append(
            {
                "output_surface": name,
                "row_count": len(surface_rows),
                "status": status,
                "basis": "phase02_evidence_intake",
                "notes": notes,
            }
        )
    return rows


def _flag_index(rows: list[dict[str, object]]) -> set[str]:
    return {str(row.get("relation_anchor_id", "")) for row in rows}


def _pair_key(left: str, right: str) -> str:
    first, second = sorted([left, right])
    return f"{first}|{second}"


def _window_text(row: dict[str, str], start_field: str, end_field: str) -> str:
    start = row.get(start_field, "")
    end = row.get(end_field, "")
    if start == "" and end == "":
        return ""
    return f"{start}|{end}"


def _sign_text(value: float | None) -> str:
    if value is None:
        return ""
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def _direction_text(value: str) -> str:
    numeric = as_float(value)
    if numeric is not None:
        return _sign_text(numeric)
    return value


def _success_manifest(resolved: ResolvedPhase02Paths) -> dict[str, object]:
    return {
        "phase": "phase02",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase01b_runtime": str(resolved.phase01b_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase02_relation_evidence_intake_complete_waiting_for_phase03_plan",
        "phase02_completion_decision": PHASE02_APPROVED_COMPLETION_STATE,
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase02",
        "phase_scope": "relation_evidence_intake_only",
        "controller_sha": PHASE02_CONTROLLER_SHA,
        "forbidden_outputs_absent": "yes",
        "outputs": list(PHASE02_REQUIRED_OUTPUTS),
    }


def _blocked_manifest(resolved: ResolvedPhase02Paths) -> dict[str, object]:
    return {
        "phase": "phase02",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase01b_runtime": str(resolved.phase01b_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase02_relation_evidence_intake_blocked",
        "phase02_completion_decision": PHASE02_BLOCKED_STATE,
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase02",
        "phase_scope": "relation_evidence_intake_only",
        "controller_sha": PHASE02_CONTROLLER_SHA,
        "forbidden_outputs_absent": "yes",
        "outputs": [],
    }


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


def _preferred_kinetic_output_order() -> list[str]:
    return [
        "relation_anchor_id",
        "source_surface",
        "source_row_key",
        "branch",
        "canonical_component_id",
        "scenario_canonical",
        "condition_role",
        "condition_id",
        "replicate",
        "time_window_or_interval",
        "kinetic_measure_type",
        "kinetic_value",
        "kinetic_direction",
        "kinetic_role",
        "kinetic_support_status",
        "direct_read_yes_no",
        "trace_id",
    ]


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
