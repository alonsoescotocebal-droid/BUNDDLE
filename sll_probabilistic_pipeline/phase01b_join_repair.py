"""Phase 01B join root-cause repair runtime."""

from __future__ import annotations

from pathlib import Path

from .config import PHASE01A_OUTPUTS, PHASE01B_JOIN_REPAIR_REQUIRED_OUTPUTS
from .paths import ResolvedPhase01BJoinRepairPaths, resolve_phase01b_join_repair_paths
from .standardize.joins import build_join_resolution_bundle, join_output_preferred_order
from .utils import (
    ensure_dir,
    fieldnames_from_rows,
    path_snapshot,
    read_json,
    read_tsv,
    read_tsv_with_header,
    utc_now_iso,
    write_json,
    write_tsv,
)
from .validation.phase01b_join_repair import build_phase01b_join_repair_validation_summary


REQUIRED_RUNTIME_DATA_SURFACES = (
    "stat_descriptive_node_state_long.tsv",
    "kinetic_rate_primary_long.tsv",
    "kinetic_temporal_coupling_primary_long.tsv",
    "kinetic_growth_primary_long.tsv",
)


def run_phase01b_join_repair(
    *,
    repo_root: str | Path,
    phase01b_runtime: str | Path,
    out_root: str | Path,
    strict: bool,
) -> dict[str, object]:
    repo_snapshot_before = path_snapshot(Path(repo_root).resolve(strict=False))
    resolved = resolve_phase01b_join_repair_paths(
        repo_root=repo_root,
        phase01b_runtime=phase01b_runtime,
        out_root=out_root,
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
            "notes": "Phase 01B join repair runtime created under allowed external results root.",
        }
    ]
    _write_table(
        audit_dir / "output_root_boundary_audit.tsv",
        output_root_boundary_rows,
        preferred_order=list(output_root_boundary_rows[0].keys()),
    )

    input_manifest = read_json(resolved.input_manifest)
    input_validation_rows = read_tsv(resolved.input_validation_summary)
    preflight = _preflight_input_runtime(
        resolved=resolved,
        input_manifest=input_manifest,
        input_validation_rows=input_validation_rows,
        strict=strict,
    )

    original_join_rows, original_join_header = read_tsv_with_header(resolved.input_join_audit)
    _write_table(
        data_dir / "input_join_key_audit_original.tsv",
        original_join_rows,
        preferred_order=original_join_header,
    )

    phase01a_policy_rows = _load_phase01a_policy_rows(resolved.phase01b_runtime)
    stat_outputs, kinetic_outputs = _load_phase01b_runtime_surfaces(resolved.phase01b_runtime)
    join_bundle = build_join_resolution_bundle(
        phase01a_policy_rows=phase01a_policy_rows,
        stat_outputs=stat_outputs,
        kinetic_outputs=kinetic_outputs,
    )

    for filename, rows in join_bundle.items():
        _write_table(
            data_dir / filename,
            rows,
            preferred_order=_preferred_order_for_output(filename),
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

    final_decision = _final_decision(join_bundle)
    manifest = {
        "phase": "phase01b_join_repair",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(resolved.repo_root),
        "phase01b_runtime": str(resolved.phase01b_runtime),
        "out_root": str(resolved.requested_out_root),
        "runtime_root": str(resolved.runtime_root),
        "phase_status": "phase01b_join_root_cause_repair_complete",
        "pipeline_global_status": "not_closed",
        "final_go_no_go": "not_applicable_for_join_repair",
        "phase02_plan_decision": final_decision,
        "input_phase01b_warning_rows": preflight["warning_count"],
        "outputs": list(PHASE01B_JOIN_REPAIR_REQUIRED_OUTPUTS),
    }
    write_json(manifest_dir / "runtime_manifest.json", manifest)

    validation_path = audit_dir / "many_to_many_root_cause_validation_summary.tsv"
    required_for_validation = tuple(
        relative_path
        for relative_path in PHASE01B_JOIN_REPAIR_REQUIRED_OUTPUTS
        if relative_path != "audit/many_to_many_root_cause_validation_summary.tsv"
    )
    validation_rows = build_phase01b_join_repair_validation_summary(
        runtime_root=runtime_root,
        required_outputs=required_for_validation,
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        input_manifest=input_manifest,
        input_warning_count=preflight["warning_count"],
        input_disallowed_warning_count=preflight["disallowed_warning_count"],
        join_bundle=join_bundle,
        final_decision=final_decision,
    )
    _write_table(
        validation_path,
        validation_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    validation_rows = build_phase01b_join_repair_validation_summary(
        runtime_root=runtime_root,
        required_outputs=PHASE01B_JOIN_REPAIR_REQUIRED_OUTPUTS,
        output_root_boundary_rows=output_root_boundary_rows,
        repo_contamination_rows=repo_contamination_rows,
        input_manifest=input_manifest,
        input_warning_count=preflight["warning_count"],
        input_disallowed_warning_count=preflight["disallowed_warning_count"],
        join_bundle=join_bundle,
        final_decision=final_decision,
    )
    _write_table(
        validation_path,
        validation_rows,
        preferred_order=["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
    )
    return manifest


def _load_phase01a_policy_rows(runtime_root: Path) -> dict[str, list[dict[str, object]]]:
    return {
        filename: read_tsv(runtime_root / "data" / filename)
        for filename in PHASE01A_OUTPUTS
    }


def _load_phase01b_runtime_surfaces(
    runtime_root: Path,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    stat_outputs = {
        "stat_descriptive_node_state_long.tsv": read_tsv(runtime_root / "data" / "stat_descriptive_node_state_long.tsv"),
    }
    kinetic_outputs = {
        "kinetic_rate_primary_long.tsv": read_tsv(runtime_root / "data" / "kinetic_rate_primary_long.tsv"),
        "kinetic_temporal_coupling_primary_long.tsv": read_tsv(
            runtime_root / "data" / "kinetic_temporal_coupling_primary_long.tsv"
        ),
        "kinetic_growth_primary_long.tsv": read_tsv(runtime_root / "data" / "kinetic_growth_primary_long.tsv"),
    }
    return stat_outputs, kinetic_outputs


def _preflight_input_runtime(
    *,
    resolved: ResolvedPhase01BJoinRepairPaths,
    input_manifest: dict[str, object],
    input_validation_rows: list[dict[str, str]],
    strict: bool,
) -> dict[str, int]:
    manifest_ok = (
        input_manifest.get("phase") == "phase01b"
        and input_manifest.get("phase_status") == "phase01b_complete_waiting_for_phase02_approval"
        and input_manifest.get("pipeline_global_status") == "not_closed"
        and input_manifest.get("final_go_no_go") == "not_applicable_for_phase01b"
    )
    if not manifest_ok:
        raise RuntimeError(f"Input Phase 01B runtime manifest is not approved: {resolved.input_manifest}")

    fail_rows = [
        row
        for row in input_validation_rows
        if row.get("status") == "FAIL" or row.get("severity") == "error"
    ]
    warning_rows = [
        row
        for row in input_validation_rows
        if row.get("status") == "WARN" or row.get("severity") == "warning"
    ]
    disallowed_warning_rows = [
        row for row in warning_rows if row.get("check_id") != "join_many_to_many_risk_profiled_not_joined"
    ]
    legacy_warning_rows = [
        row for row in warning_rows if row.get("check_id") == "join_many_to_many_risk_profiled_not_joined"
    ]
    if fail_rows:
        raise RuntimeError(
            "Input Phase 01B runtime contains error-level failures: "
            + "; ".join(row.get("check_id", "") for row in fail_rows)
        )
    if disallowed_warning_rows:
        raise RuntimeError(
            "Input Phase 01B runtime contains disallowed warnings: "
            + "; ".join(row.get("check_id", "") for row in disallowed_warning_rows)
        )
    if strict and len(legacy_warning_rows) > 1:
        raise RuntimeError("Input Phase 01B runtime contains multiple legacy join warnings.")

    for filename in REQUIRED_RUNTIME_DATA_SURFACES:
        path = resolved.phase01b_runtime / "data" / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required Phase 01B runtime surface: {path}")

    return {
        "warning_count": len(warning_rows),
        "disallowed_warning_count": len(disallowed_warning_rows),
    }


def _final_decision(join_bundle: dict[str, list[dict[str, object]]]) -> str:
    join_rows = [
        row
        for row in join_bundle["input_join_key_audit.tsv"]
        if row.get("left_surface") != "cross_layer_join_identity_policy.tsv"
    ]
    all_resolved = all(row.get("resolution_state") == "resolved" for row in join_rows)
    admissible = all(
        row.get("join_admissibility") in {"joinable", "projection_only", "policy_lookup_only", "forbidden"}
        for row in join_rows
    )
    registry_ok = any(
        row.get("surface_name") == "growth_variable_identity_audit.tsv"
        and row.get("non_joinable_as_measurement") == "yes"
        for row in join_bundle["policy_surface_non_joinable_registry.tsv"]
    )
    return "PHASE02_PLAN_ALLOWED" if all_resolved and admissible and registry_ok else "PHASE02_BLOCKED_BY_JOIN_ROOT_CAUSE"


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
    return join_output_preferred_order(filename)


def _write_table(path: Path, rows: list[dict[str, object]], *, preferred_order: list[str]) -> None:
    write_tsv(path, rows, fieldnames_from_rows(rows, preferred_order))
