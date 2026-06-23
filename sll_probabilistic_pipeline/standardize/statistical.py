"""Statistical normalization for Phase 01B."""

from __future__ import annotations

from collections.abc import Iterable

from ..io.readers import LoadedSurface
from ..paths import canonicalize_scenario, classify_condition_role
from ..utils import normalize_label, stable_trace_id


def _alias_lookup(alias_rows: list[dict[str, str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in alias_rows:
        lookup.setdefault(normalize_label(row["raw_label"]), row["canonical_component_id"])
    return lookup


def _canonical_component(raw_label: str, alias_lookup: dict[str, str]) -> str:
    return alias_lookup.get(normalize_label(raw_label), raw_label)


def _value_type_for_component(raw_label: str, canonical_component_id: str) -> str:
    if canonical_component_id == "growth_node":
        if raw_label == "lnOD":
            return "lnOD"
        if raw_label == "OD600":
            return "raw_OD600"
        if raw_label == "ln(abs-abs0)":
            return "ln_abs_minus_abs0"
        return "growth_context"
    return "concentration_g_per_L"


def _base_trace(
    *,
    source_path: str,
    source_surface: str,
    source_row_key: str,
    source_row_number: int,
) -> dict[str, object]:
    return {
        "source_path": source_path,
        "source_surface": source_surface,
        "source_row_key": source_row_key,
        "source_row_number": source_row_number,
        "direct_read_yes_no": "yes",
        "inference_used_yes_no": "no",
        "trace_id": stable_trace_id(source_surface, source_row_key, source_row_number),
    }


def build_statistical_outputs(
    stat_surfaces: dict[int, dict[str, LoadedSurface]],
    alias_rows: list[dict[str, str]],
) -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    alias_lookup = _alias_lookup(alias_rows)
    edge_rows: list[dict[str, object]] = []
    model_context_rows: list[dict[str, object]] = []
    descriptive_rows: list[dict[str, object]] = []
    interdependence_rows: list[dict[str, object]] = []
    conditioned_rows: list[dict[str, object]] = []
    provenance_rows: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for run_max_lag, loaded in sorted(stat_surfaces.items()):
        branch_or_run = loaded["effects"].branch_or_run
        effects = loaded["effects"]
        for row_number, row in enumerate(effects.rows, start=1):
            source_raw = row["source"]
            target_raw = row["target"]
            edge_lag = int(row["lag"])
            condition_role = classify_condition_role(row["condition_id"], "", row.get("family", ""))
            source_row_key = "|".join(
                [row["condition_id"], row["scenario"], row["replicate"], source_raw, target_raw, row["lag"]]
            )
            edge_rows.append(
                {
                    "source_layer": "statistical",
                    "run_folder": branch_or_run,
                    "run_max_lag": run_max_lag,
                    "edge_lag": edge_lag,
                    "condition_id": row["condition_id"],
                    "scenario": row["scenario"],
                    "scenario_canonical": canonicalize_scenario(row["scenario"]),
                    "condition_role": condition_role,
                    "family": row["family"],
                    "level": row["level"],
                    "replicate": row["replicate"],
                    "source_variable_raw": source_raw,
                    "target_variable_raw": target_raw,
                    "source_canonical_component_id": _canonical_component(source_raw, alias_lookup),
                    "target_canonical_component_id": _canonical_component(target_raw, alias_lookup),
                    "value_type": "pcmci_effect",
                    "evidence_scope": "directed_relation",
                    "effect": row["effect"],
                    "q_value": row["q_value"],
                    "time_axis": row["time_axis"],
                    "effective_timepoint_count": row["effective_timepoint_count"],
                    "gate": row["gate"],
                    "reason": row["reason"],
                    **_base_trace(
                        source_path=str(effects.path),
                        source_surface="results/effects.tsv",
                        source_row_key=source_row_key,
                        source_row_number=row_number,
                    ),
                }
            )
            status = "PASS" if edge_lag <= run_max_lag else "FAIL"
            validation_rows.append(
                {
                    "check_id": "edge_lag_le_run_max_lag",
                    "status": status,
                    "severity": "error" if status == "FAIL" else "info",
                    "source_surface": "results/effects.tsv",
                    "source_row_key": source_row_key,
                    "details": f"edge_lag={edge_lag};run_max_lag={run_max_lag}",
                }
            )

        network = loaded["network_partialcorr"]
        for row_number, row in enumerate(network.rows, start=1):
            condition_role = classify_condition_role(row.get("condition_id", ""), "", row.get("family", ""))
            left_raw = row["var_i"]
            right_raw = row["var_j"]
            source_row_key = "|".join([branch_or_run, left_raw, right_raw, str(row_number)])
            conditioned_rows.append(
                {
                    "source_layer": "statistical",
                    "run_folder": branch_or_run,
                    "run_max_lag": run_max_lag,
                    "scenario_canonical": "",
                    "condition_role": condition_role,
                    "variable_i_raw": left_raw,
                    "variable_j_raw": right_raw,
                    "variable_i_canonical_component_id": _canonical_component(left_raw, alias_lookup),
                    "variable_j_canonical_component_id": _canonical_component(right_raw, alias_lookup),
                    "value_type": "partialcorr",
                    "evidence_scope": "undirected_pair",
                    **row,
                    **_base_trace(
                        source_path=str(network.path),
                        source_surface="results/network_partialcorr.tsv",
                        source_row_key=source_row_key,
                        source_row_number=row_number,
                    ),
                }
            )

        for context_name in ("pcmci_qc", "partialcorr_qc", "pcmci_dense_qc", "run_manifest"):
            context_surface = loaded[context_name]
            assert context_surface.json_payload is not None
            for key in sorted(context_surface.json_payload.keys()):
                model_context_rows.append(
                    {
                        "source_layer": "statistical",
                        "run_folder": branch_or_run,
                        "run_max_lag": run_max_lag,
                        "context_group": context_name,
                        "context_key": key,
                        "context_value": context_surface.json_payload[key],
                        "source_path": str(context_surface.path),
                        "source_surface": context_surface.source_surface,
                        "trace_id": stable_trace_id(branch_or_run, context_name, key),
                    }
                )
        for context_name in ("postrun_statistical_audits", "availability_matrix", "schema_check"):
            context_surface = loaded[context_name]
            for row_number, row in enumerate(context_surface.rows, start=1):
                context_key = "|".join(f"{name}={value}" for name, value in row.items() if value != "")
                model_context_rows.append(
                    {
                        "source_layer": "statistical",
                        "run_folder": branch_or_run,
                        "run_max_lag": run_max_lag,
                        "context_group": context_name,
                        "context_key": context_key,
                        "context_value": row,
                        "source_path": str(context_surface.path),
                        "source_surface": context_surface.source_surface,
                        "source_row_number": row_number,
                        "trace_id": stable_trace_id(branch_or_run, context_name, row_number, context_key),
                    }
                )

        interdependence = loaded["interdependence_windows"]
        for row_number, row in enumerate(interdependence.rows, start=1):
            condition_role = classify_condition_role(row["condition_id"], "", row.get("family", ""))
            source_row_key = "|".join(
                [row["condition_id"], row["scenario"], row["variable_i"], row["variable_j"], row["window"]]
            )
            interdependence_rows.append(
                {
                    "source_layer": "statistical",
                    "run_folder": branch_or_run,
                    "run_max_lag": run_max_lag,
                    "scenario_canonical": canonicalize_scenario(row["scenario"]),
                    "condition_role": condition_role,
                    "variable_i_canonical_component_id": _canonical_component(row["variable_i"], alias_lookup),
                    "variable_j_canonical_component_id": _canonical_component(row["variable_j"], alias_lookup),
                    "value_type": "window_delta",
                    "evidence_scope": "undirected_pair",
                    **row,
                    **_base_trace(
                        source_path=str(interdependence.path),
                        source_surface="results/interdependence_windows.tsv",
                        source_row_key=source_row_key,
                        source_row_number=row_number,
                    ),
                }
            )

        snapshots = loaded["snapshots"]
        for row_number, row in enumerate(snapshots.rows, start=1):
            condition_role = classify_condition_role(row["condition_id"], "", row.get("family", ""))
            raw_label = row["variable"]
            canonical_component_id = _canonical_component(raw_label, alias_lookup)
            value_type = _value_type_for_component(raw_label, canonical_component_id)
            for key, value in row.items():
                if not key.startswith("value_"):
                    continue
                timepoint_label = key.removeprefix("value_")
                source_row_key = "|".join(
                    [row["condition_id"], row["scenario"], row["replicate"], raw_label, timepoint_label]
                )
                descriptive_rows.append(
                    {
                        "source_layer": "statistical",
                        "run_folder": branch_or_run,
                        "run_max_lag": run_max_lag,
                        "scenario_canonical": canonicalize_scenario(row["scenario"]),
                        "condition_role": condition_role,
                        "descriptive_measure_type": "snapshot_value",
                        "timepoint_label": timepoint_label,
                        "window_label": "",
                        "variable_raw": raw_label,
                        "canonical_component_id": canonical_component_id,
                        "value_type": value_type,
                        "evidence_scope": "target_state",
                        "metric_value": value,
                        "gate": row["gate"],
                        "reason": row["reason"],
                        "condition_id": row["condition_id"],
                        "scenario": row["scenario"],
                        "family": row["family"],
                        "level": row["level"],
                        "replicate": row["replicate"],
                        **_base_trace(
                            source_path=str(snapshots.path),
                            source_surface="tables/snapshots.tsv",
                            source_row_key=source_row_key,
                            source_row_number=row_number,
                        ),
                    }
                )

        window_deltas = loaded["window_deltas"]
        for row_number, row in enumerate(window_deltas.rows, start=1):
            condition_role = classify_condition_role(row["condition_id"], "", row.get("family", ""))
            raw_label = row["variable"]
            canonical_component_id = _canonical_component(raw_label, alias_lookup)
            value_type = _value_type_for_component(raw_label, canonical_component_id)
            for key, value in row.items():
                if not key.startswith("delta_"):
                    continue
                window_label = key.removeprefix("delta_")
                source_row_key = "|".join(
                    [row["condition_id"], row["scenario"], row["replicate"], raw_label, window_label]
                )
                descriptive_rows.append(
                    {
                        "source_layer": "statistical",
                        "run_folder": branch_or_run,
                        "run_max_lag": run_max_lag,
                        "scenario_canonical": canonicalize_scenario(row["scenario"]),
                        "condition_role": condition_role,
                        "descriptive_measure_type": "window_delta",
                        "timepoint_label": "",
                        "window_label": window_label,
                        "variable_raw": raw_label,
                        "canonical_component_id": canonical_component_id,
                        "value_type": value_type,
                        "evidence_scope": "target_state",
                        "metric_value": value,
                        "gate": row["gate"],
                        "reason": row["reason"],
                        "condition_id": row["condition_id"],
                        "scenario": row["scenario"],
                        "family": row["family"],
                        "level": row["level"],
                        "replicate": row["replicate"],
                        **_base_trace(
                            source_path=str(window_deltas.path),
                            source_surface="tables/window_deltas.tsv",
                            source_row_key=source_row_key,
                            source_row_number=row_number,
                        ),
                    }
                )

        provenance_rows.extend(
            _build_provenance_rows(
                loaded["pcmci_dense_replicate_input"],
                branch_or_run,
                run_max_lag,
                alias_lookup,
                provenance_kind="dense_input",
            )
        )
        provenance_rows.extend(
            _build_provenance_rows(
                loaded["dense_series_interpolated"],
                branch_or_run,
                run_max_lag,
                alias_lookup,
                provenance_kind="dense_interpolated",
            )
        )
        provenance_rows.extend(
            _build_provenance_rows(
                loaded["analysis_view_observed"],
                branch_or_run,
                run_max_lag,
                alias_lookup,
                provenance_kind="observed_anchor",
            )
        )
        provenance_rows.extend(
            _build_provenance_rows(
                loaded["series_index"],
                branch_or_run,
                run_max_lag,
                alias_lookup,
                provenance_kind="series_index",
            )
        )

    outputs = {
        "stat_pcmci_edge_long.tsv": edge_rows,
        "stat_pcmci_model_context_long.tsv": model_context_rows,
        "stat_descriptive_node_state_long.tsv": descriptive_rows,
        "stat_interdependence_pair_window_long.tsv": interdependence_rows,
        "stat_conditioned_pair_global_long.tsv": conditioned_rows,
        "stat_dense_data_provenance_long.tsv": provenance_rows,
    }
    return outputs, validation_rows


def _build_provenance_rows(
    surface: LoadedSurface,
    branch_or_run: str,
    run_max_lag: int,
    alias_lookup: dict[str, str],
    *,
    provenance_kind: str,
) -> Iterable[dict[str, object]]:
    results: list[dict[str, object]] = []
    for row_number, row in enumerate(surface.rows, start=1):
        variable = row.get("variable", row.get("assay_id", ""))
        raw_label = row.get("assay_id", variable)
        canonical_component_id = _canonical_component(variable or raw_label, alias_lookup)
        source_row_key = (
            row.get("row_identity_id")
            or row.get("series_time_id")
            or row.get("group_key")
            or row.get("series_id")
            or f"{branch_or_run}|{provenance_kind}|{row_number}"
        )
        gate_or_status = row.get("gate") or row.get("flag") or row.get("status") or ""
        time_h = row.get("time_h") or row.get("t_min") or row.get("time_h_dense") or ""
        results.append(
            {
                "source_layer": "statistical",
                "run_folder": branch_or_run,
                "run_max_lag": run_max_lag,
                "provenance_kind": provenance_kind,
                "condition_id": row.get("condition_id", ""),
                "scenario": row.get("scenario", ""),
                "scenario_canonical": canonicalize_scenario(row.get("scenario", "")),
                "condition_role": classify_condition_role(
                    row.get("condition_id", ""),
                    row.get("paired_condition_id", ""),
                    row.get("family", ""),
                ),
                "assay_id_raw": raw_label,
                "variable_raw": variable,
                "canonical_component_id": canonical_component_id,
                "value_type": _value_type_for_component(variable or raw_label, canonical_component_id),
                "evidence_scope": "target_state",
                "time_h": time_h,
                "time_rel_dense": row.get("time_rel_dense", ""),
                "time_h_dense": row.get("time_h_dense", ""),
                "is_interpolated": row.get("is_interpolated", ""),
                "gate_or_status": gate_or_status,
                "reason": row.get("reason", ""),
                "source_time_left_h": row.get("source_time_left_h", ""),
                "source_time_right_h": row.get("source_time_right_h", ""),
                "source_flag_merge": row.get("source_flag_merge", ""),
                **_base_trace(
                    source_path=str(surface.path),
                    source_surface=surface.source_surface,
                    source_row_key=source_row_key,
                    source_row_number=row_number,
                ),
            }
        )
    return results
