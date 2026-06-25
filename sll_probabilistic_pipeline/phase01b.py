"""Phase 01B normalized input reader runtime."""

from __future__ import annotations

from pathlib import Path

from .config import (
    KINETIC_REAL_ONLY_OPTIONAL_SURFACES,
    KINETIC_REAL_ONLY_REQUIRED_SURFACES,
    PHASE01A_OUTPUTS,
    PHASE01B_REQUIRED_OUTPUTS,
    STAT_RUN_REQUIRED_SURFACES,
)
from .io.readers import (
    LoadedSurface,
    input_file_hash_row,
    load_json_surface,
    load_tsv_surface,
    schema_inventory_row,
)
from .paths import ResolvedPhase01BPaths, resolve_phase01b_paths
from .phase01a import build_phase01a_policy_artifacts, write_phase01a_policy_artifacts
from .standardize.joins import build_join_resolution_bundle, join_output_preferred_order
from .standardize.kinetic import build_kinetic_outputs
from .standardize.statistical import build_statistical_outputs
from .utils import (
    ensure_dir,
    fieldnames_from_rows,
    path_snapshot,
    utc_now_iso,
    write_json,
    write_tsv,
)
from .validation.phase01b import build_phase01b_validation_summary


def run_phase01b(
    *,
    repo_root: str | Path,
    stat_root: str | Path,
    kin_root: str | Path,
    out_root: str | Path,
    strict: bool,
) -> dict[str, object]:
    repo_snapshot_before = path_snapshot(Path(repo_root).resolve(strict=False))
    resolved = resolve_phase01b_paths(
        repo_root=repo_root,
        stat_root=stat_root,
        kin_root=kin_root,
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
            "notes": "Phase 01B runtime created under allowed external results root.",
        }
    ]
    write_tsv(
        audit_dir / "output_root_boundary_audit.tsv",
        output_root_boundary_rows,
        list(output_root_boundary_rows[0].keys()),
    )

    stat_surfaces = _load_statistical_surfaces(resolved)
    kinetic_surfaces = _load_kinetic_surfaces(resolved)

    input_hash_rows = []
    schema_rows = []
    availability_rows = []
    for loaded in _all_loaded_surfaces(stat_surfaces, kinetic_surfaces):
        input_hash_rows.append(input_file_hash_row(loaded))
        schema_rows.append(schema_inventory_row(loaded))
        availability_rows.append(_availability_row(loaded))
    availability_rows.append(
        {
            "source_layer": "kinetic",
            "branch_or_run": "real_plus_interpolated",
            "source_surface": "branch_root",
            "source_path": str(resolved.kin_real_plus_root),
            "required_yes_no": "no",
            "status": "excluded_by_canonical_rule",
            "row_count": "",
            "column_count": "",
            "notes": "real_plus_interpolated branch is inventoried only and never consumed as primary kinetic support.",
        }
    )

    input_path_rows = _build_input_path_resolution_audit(resolved)
    input_data_basis_rows = _build_input_data_basis_policy_audit()

    phase01a_artifacts, phase01a_summary = build_phase01a_policy_artifacts(stat_root, kin_root)
    write_phase01a_policy_artifacts(data_dir, phase01a_artifacts)
    phase01a_carry_forward_rows = _build_phase01a_policy_carry_forward_audit(phase01a_artifacts, phase01a_summary)

    stat_outputs, validation_rows = build_statistical_outputs(
        stat_surfaces,
        phase01a_artifacts["canonical_component_alias_registry.tsv"],
    )
    kinetic_outputs, empty_audit_rows = build_kinetic_outputs(
        kinetic_surfaces,
        phase01a_artifacts["canonical_component_alias_registry.tsv"],
    )
    join_bundle = build_join_resolution_bundle(
        phase01a_policy_rows=phase01a_artifacts,
        stat_outputs=stat_outputs,
        kinetic_outputs=kinetic_outputs,
    )

    _write_table(
        manifest_dir / "input_file_sha256.tsv",
        input_hash_rows,
        preferred_order=["source_layer", "branch_or_run", "source_surface", "source_path", "sha256"],
    )
    _write_table(
        data_dir / "input_path_resolution_audit.tsv",
        input_path_rows,
        preferred_order=list(input_path_rows[0].keys()),
    )
    _write_table(
        data_dir / "input_surface_availability_audit.tsv",
        availability_rows,
        preferred_order=list(availability_rows[0].keys()),
    )
    _write_table(
        data_dir / "input_schema_inventory.tsv",
        schema_rows,
        preferred_order=list(schema_rows[0].keys()),
    )
    _write_table(
        data_dir / "input_data_basis_policy_audit.tsv",
        input_data_basis_rows,
        preferred_order=list(input_data_basis_rows[0].keys()),
    )
    _write_table(
        data_dir / "phase01a_policy_carry_forward_audit.tsv",
        phase01a_carry_forward_rows,
        preferred_order=list(phase01a_carry_forward_rows[0].keys()),
    )
    for filename, rows in stat_outputs.items():
        _write_table(
            data_dir / filename,
            rows,
            preferred_order=_preferred_order_for_output(filename),
        )
    for filename, rows in kinetic_outputs.items():
        _write_table(
            data_dir / filename,
            rows,
            preferred_order=_preferred_order_for_output(filename),
        )
    for filename, rows in join_bundle.items():
        _write_table(
            data_dir / filename,
            rows,
            preferred_order=_preferred_order_for_output(filename),
        )
    _write_table(
        data_dir / "input_empty_surface_audit.tsv",
        empty_audit_rows or [
            {
                "source_layer": "",
                "branch_or_run": "",
                "source_surface": "",
                "source_path": "",
                "empty_status": "none_observed",
                "row_count": "",
                "basis": "",
                "notes": "",
            }
        ],
        preferred_order=["source_layer", "branch_or_run", "source_surface", "source_path", "empty_status", "row_count", "basis", "notes"],
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

    manifest = {
        "phase": "phase01b",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "stat_root": str(resolved.stat_root),
        "kin_root": str(resolved.kin_root),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase01b_complete_waiting_for_phase02_approval",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_phase01b",
        "outputs": list(PHASE01B_REQUIRED_OUTPUTS),
        "phase01a_identity_go_state": phase01a_summary["identity_go_state_if_full_release_were_attempted"],
    }
    write_json(manifest_dir / "runtime_manifest.json", manifest)

    validation_path = audit_dir / "phase01b_validation_summary.tsv"
    required_for_validation = tuple(
        relative_path
        for relative_path in PHASE01B_REQUIRED_OUTPUTS
        if relative_path != "audit/phase01b_validation_summary.tsv"
    )
    validation_summary_rows = build_phase01b_validation_summary(
        validation_rows=validation_rows,
        runtime_root=runtime_root,
        required_outputs=required_for_validation,
        discovered_lags=sorted(stat_surfaces.keys()),
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        manifest=manifest,
        phase01a_carry_forward_rows=phase01a_carry_forward_rows,
        availability_rows=availability_rows,
        join_bundle=join_bundle,
        stat_outputs=stat_outputs,
        kinetic_outputs=kinetic_outputs,
        empty_audit_rows=empty_audit_rows,
    )
    _write_table(
        validation_path,
        validation_summary_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    validation_summary_rows = build_phase01b_validation_summary(
        validation_rows=validation_rows,
        runtime_root=runtime_root,
        required_outputs=PHASE01B_REQUIRED_OUTPUTS,
        discovered_lags=sorted(stat_surfaces.keys()),
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        manifest=manifest,
        phase01a_carry_forward_rows=phase01a_carry_forward_rows,
        availability_rows=availability_rows,
        join_bundle=join_bundle,
        stat_outputs=stat_outputs,
        kinetic_outputs=kinetic_outputs,
        empty_audit_rows=empty_audit_rows,
    )
    _write_table(
        validation_path,
        validation_summary_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    return manifest


def _load_statistical_surfaces(resolved: ResolvedPhase01BPaths) -> dict[int, dict[str, LoadedSurface]]:
    results: dict[int, dict[str, LoadedSurface]] = {}
    for run_max_lag, run in sorted(resolved.stat_runs.items()):
        branch_or_run = run.run_folder.name
        results[run_max_lag] = {
            "effects": load_tsv_surface(run.effects, source_layer="statistical", source_surface="results/effects.tsv", branch_or_run=branch_or_run),
            "network_partialcorr": load_tsv_surface(run.network_partialcorr, source_layer="statistical", source_surface="results/network_partialcorr.tsv", branch_or_run=branch_or_run),
            "interdependence_windows": load_tsv_surface(run.interdependence_windows, source_layer="statistical", source_surface="results/interdependence_windows.tsv", branch_or_run=branch_or_run),
            "snapshots": load_tsv_surface(run.snapshots, source_layer="statistical", source_surface="tables/snapshots.tsv", branch_or_run=branch_or_run),
            "window_deltas": load_tsv_surface(run.window_deltas, source_layer="statistical", source_surface="tables/window_deltas.tsv", branch_or_run=branch_or_run),
            "pcmci_dense_replicate_input": load_tsv_surface(run.pcmci_dense_replicate_input, source_layer="statistical", source_surface="intermediate/pcmci_dense_replicate_input.tsv", branch_or_run=branch_or_run),
            "dense_series_interpolated": load_tsv_surface(run.dense_series_interpolated, source_layer="statistical", source_surface="intermediate/dense_series_interpolated.tsv", branch_or_run=branch_or_run),
            "analysis_view_observed": load_tsv_surface(run.analysis_view_observed, source_layer="statistical", source_surface="intermediate/analysis_view_observed.tsv", branch_or_run=branch_or_run),
            "postrun_statistical_audits": load_tsv_surface(run.postrun_statistical_audits, source_layer="statistical", source_surface="audit/postrun_statistical_audits.tsv", branch_or_run=branch_or_run),
            "series_index": load_tsv_surface(run.series_index, source_layer="statistical", source_surface="audit/series_index.tsv", branch_or_run=branch_or_run),
            "availability_matrix": load_tsv_surface(run.availability_matrix, source_layer="statistical", source_surface="audit/availability_matrix.tsv", branch_or_run=branch_or_run),
            "schema_check": load_tsv_surface(run.schema_check, source_layer="statistical", source_surface="qc/schema_check.tsv", branch_or_run=branch_or_run),
            "pcmci_qc": load_json_surface(run.pcmci_qc, source_layer="statistical", source_surface="audit/pcmci_qc.json", branch_or_run=branch_or_run),
            "partialcorr_qc": load_json_surface(run.partialcorr_qc, source_layer="statistical", source_surface="audit/partialcorr_qc.json", branch_or_run=branch_or_run),
            "pcmci_dense_qc": load_json_surface(run.pcmci_dense_qc, source_layer="statistical", source_surface="audit/pcmci_dense_qc.json", branch_or_run=branch_or_run),
            "run_manifest": load_json_surface(run.run_manifest, source_layer="statistical", source_surface="manifest/run_manifest.json", branch_or_run=branch_or_run),
        }
    return results


def _load_kinetic_surfaces(resolved: ResolvedPhase01BPaths) -> dict[str, LoadedSurface]:
    root = resolved.kin_real_only_root
    return {
        "growth_windows_handoff": load_tsv_surface(root / "95_audit" / "growth_windows_handoff.tsv", source_layer="kinetic", source_surface="95_audit/growth_windows_handoff.tsv", branch_or_run="real_only"),
        "metabolite_interval_rates_handoff": load_tsv_surface(root / "95_audit" / "metabolite_interval_rates_handoff.tsv", source_layer="kinetic", source_surface="95_audit/metabolite_interval_rates_handoff.tsv", branch_or_run="real_only"),
        "temporal_coupling_classification_handoff": load_tsv_surface(root / "95_audit" / "temporal_coupling_classification_handoff.tsv", source_layer="kinetic", source_surface="95_audit/temporal_coupling_classification_handoff.tsv", branch_or_run="real_only"),
        "yield_pairs_handoff": load_tsv_surface(root / "95_audit" / "yield_pairs_handoff.tsv", source_layer="kinetic", source_surface="95_audit/yield_pairs_handoff.tsv", branch_or_run="real_only"),
        "growth_window_audit": load_tsv_surface(root / "95_audit" / "growth_window_audit.tsv", source_layer="kinetic", source_surface="95_audit/growth_window_audit.tsv", branch_or_run="real_only"),
        "metabolite_rate_audit": load_tsv_surface(root / "95_audit" / "metabolite_rate_audit.tsv", source_layer="kinetic", source_surface="95_audit/metabolite_rate_audit.tsv", branch_or_run="real_only"),
        "kinetic_replicate_consensus_audit": load_tsv_surface(root / "95_audit" / "kinetic_replicate_consensus_audit.tsv", source_layer="kinetic", source_surface="95_audit/kinetic_replicate_consensus_audit.tsv", branch_or_run="real_only"),
        "yield_audit": load_tsv_surface(root / "95_audit" / "yield_audit.tsv", source_layer="kinetic", source_surface="95_audit/yield_audit.tsv", branch_or_run="real_only"),
        "growth_source_audit": load_tsv_surface(root / "93_growth_windows" / "growth_source_audit.tsv", source_layer="kinetic", source_surface="93_growth_windows/growth_source_audit.tsv", branch_or_run="real_only"),
        "growth_windows_best": load_tsv_surface(root / "93_growth_windows" / "growth_windows_best.tsv", source_layer="kinetic", source_surface="93_growth_windows/growth_windows_best.tsv", branch_or_run="real_only"),
        "metabolite_interval_rates": load_tsv_surface(root / "94_accessible_kinetics" / "metabolite_interval_rates.tsv", source_layer="kinetic", source_surface="94_accessible_kinetics/metabolite_interval_rates.tsv", branch_or_run="real_only"),
        "partial_mass_balance": load_tsv_surface(root / "94_accessible_kinetics" / "partial_mass_balance.tsv", source_layer="kinetic", source_surface="94_accessible_kinetics/partial_mass_balance.tsv", branch_or_run="real_only"),
        "methodological_exclusions": load_tsv_surface(root / "94_accessible_kinetics" / "methodological_exclusions.tsv", source_layer="kinetic", source_surface="94_accessible_kinetics/methodological_exclusions.tsv", branch_or_run="real_only"),
        "report_output_catalog": load_tsv_surface(resolved.kin_report_output_catalog, source_layer="kinetic", source_surface="report_output_catalog.tsv", branch_or_run="catalog"),
        "report_contract_metrics": load_tsv_surface(resolved.kin_report_contract_metrics, source_layer="kinetic", source_surface="report_contract_metrics.tsv", branch_or_run="catalog"),
        "report_contract_summary": load_json_surface(resolved.kin_report_contract_summary, source_layer="kinetic", source_surface="report_contract_summary.json", branch_or_run="catalog"),
    }


def _all_loaded_surfaces(
    stat_surfaces: dict[int, dict[str, LoadedSurface]],
    kinetic_surfaces: dict[str, LoadedSurface],
) -> list[LoadedSurface]:
    all_surfaces: list[LoadedSurface] = []
    for loaded in stat_surfaces.values():
        all_surfaces.extend(loaded.values())
    all_surfaces.extend(kinetic_surfaces.values())
    return all_surfaces


def _availability_row(loaded: LoadedSurface) -> dict[str, object]:
    if loaded.source_surface == "95_audit/yield_pairs_handoff.tsv" and loaded.row_count == 0:
        status = "empty_legitimate"
        notes = "Header-only yield handoff retained as legitimate empty surface."
    else:
        status = "available"
        notes = ""
    required_yes_no = "no" if loaded.source_surface in KINETIC_REAL_ONLY_OPTIONAL_SURFACES else "yes"
    return {
        "source_layer": loaded.source_layer,
        "branch_or_run": loaded.branch_or_run,
        "source_surface": loaded.source_surface,
        "source_path": str(loaded.path),
        "required_yes_no": required_yes_no,
        "status": status,
        "row_count": loaded.row_count,
        "column_count": loaded.column_count,
        "notes": notes,
    }


def _build_input_path_resolution_audit(resolved: ResolvedPhase01BPaths) -> list[dict[str, object]]:
    rows = [
        {
            "requested_role": "stat_root",
            "requested_path": str(resolved.stat_root),
            "resolved_path": str(resolved.stat_root),
            "exists_yes_no": "yes",
            "candidate_count": 1,
            "selected_yes_no": "yes",
            "deviation_reason": "",
            "decision": "explicit_root_used",
        },
        {
            "requested_role": "kin_root",
            "requested_path": str(resolved.kin_root),
            "resolved_path": str(resolved.kin_root),
            "exists_yes_no": "yes",
            "candidate_count": 1,
            "selected_yes_no": "yes",
            "deviation_reason": "",
            "decision": "explicit_root_used",
        },
    ]
    for lag, run in sorted(resolved.stat_runs.items()):
        rows.append(
            {
                "requested_role": f"stat_run_lag{lag:02d}",
                "requested_path": str(resolved.stat_root),
                "resolved_path": str(run.run_folder),
                "exists_yes_no": "yes",
                "candidate_count": 1,
                "selected_yes_no": "yes",
                "deviation_reason": "",
                "decision": "strict_unique_lag_folder",
            }
        )
    rows.append(
        {
            "requested_role": "kin_real_only_branch",
            "requested_path": str(resolved.kin_root),
            "resolved_path": str(resolved.kin_real_only_root),
            "exists_yes_no": "yes",
            "candidate_count": 1,
            "selected_yes_no": "yes",
            "deviation_reason": "",
            "decision": "canonical_enabled_branch",
        }
    )
    rows.append(
        {
            "requested_role": "kin_real_plus_interpolated_branch",
            "requested_path": str(resolved.kin_root),
            "resolved_path": str(resolved.kin_real_plus_root),
            "exists_yes_no": "yes",
            "candidate_count": 1,
            "selected_yes_no": "no",
            "deviation_reason": "excluded_by_canonical_rule",
            "decision": "inventory_only_disabled_branch",
        }
    )
    return rows


def _build_input_data_basis_policy_audit() -> list[dict[str, object]]:
    return [
        {
            "source_layer": "statistical",
            "basis_rule": "audited_interpolated_dense_matrix_anchored_to_real_observations",
            "enabled_branch": "LAG01-LAG04 statistical runs",
            "status": "enabled_with_traceability",
            "notes": "Interpolated/dense data retained only with provenance and audit fields.",
        },
        {
            "source_layer": "kinetic",
            "basis_rule": "real_only_experimental_observations",
            "enabled_branch": "SLL_20260426_133037_real_only",
            "status": "enabled_primary",
            "notes": "Primary kinetic normalized outputs use real_only only.",
        },
        {
            "source_layer": "kinetic",
            "basis_rule": "real_plus_interpolated_disabled",
            "enabled_branch": "SLL_20260426_133037_real_plus_interpolated",
            "status": "excluded_by_canonical_rule",
            "notes": "Inventory only; never used for kinetic support or primary outputs.",
        },
    ]


def _build_phase01a_policy_carry_forward_audit(
    artifacts: dict[str, list[dict[str, object]]],
    summary: dict[str, object],
) -> list[dict[str, object]]:
    rows = []
    for filename in PHASE01A_OUTPUTS:
        rows.append(
            {
                "artifact_name": filename,
                "status": "present_and_usable",
                "source_mode": "executed_phase01a_builder",
                "immutable_policy_yes_no": "yes",
                "row_count": len(artifacts[filename]),
                "identity_go_state_if_full_release_were_attempted": summary[
                    "identity_go_state_if_full_release_were_attempted"
                ],
                "notes": "Carried forward into Phase 01B runtime without semantic reinterpretation.",
            }
        )
    return rows


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


def _preferred_order_for_output(filename: str) -> list[str]:
    join_order = join_output_preferred_order(filename)
    if join_order:
        return join_order
    if filename == "stat_pcmci_edge_long.tsv":
        return [
            "source_layer",
            "run_folder",
            "run_max_lag",
            "edge_lag",
            "condition_id",
            "scenario",
            "scenario_canonical",
            "condition_role",
            "source_variable_raw",
            "target_variable_raw",
            "source_canonical_component_id",
            "target_canonical_component_id",
            "value_type",
            "evidence_scope",
            "effect",
            "q_value",
            "source_path",
            "source_surface",
            "source_row_key",
            "source_row_number",
            "trace_id",
        ]
    if filename == "kinetic_yield_primary_long.tsv":
        return [
            "source_layer",
            "branch",
            "condition_id",
            "scenario",
            "scenario_canonical",
            "condition_role",
            "substrate_canonical_component_id",
            "product_canonical_component_id",
            "value_type",
            "evidence_scope",
            "group_key",
            "source_path",
            "source_surface",
            "source_row_key",
            "source_row_number",
            "trace_id",
        ]
    return []


def _write_table(path: Path, rows: list[dict[str, object]], *, preferred_order: list[str]) -> None:
    write_tsv(path, rows, fieldnames_from_rows(rows, preferred_order))
