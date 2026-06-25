"""Configuration constants for the SLL probabilistic pipeline."""

from __future__ import annotations

from pathlib import Path

DEFAULT_STAT_ROOT = Path(
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs"
    r"\SLL_REAL_PCMCI_LAG01-04_20260401_174816"
)
DEFAULT_KIN_ROOT = Path(
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations"
    r"\SLL_rates_block_20260426_133037"
)
DEFAULT_RESULTS_ROOT = Path(
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS"
)

SUPPORTED_PHASES = {"phase01a", "phase01b", "phase01b_join_repair"}
PHASE01B_RUNTIME_PREFIX = "SLL_PHASE01B_NORMALIZED_INPUT_READER_"
PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX = "SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_"
PHASE01B_REPO_OUTPUT_REJECTION_CODE = "PHASE01B_OUTPUT_ROOT_INSIDE_REPO_FORBIDDEN"

PHASE01A_OUTPUTS = (
    "growth_variable_identity_audit.tsv",
    "acetate_dual_role_audit.tsv",
    "canonical_component_alias_registry.tsv",
    "component_role_by_condition_audit.tsv",
    "cross_layer_join_identity_policy.tsv",
)
PHASE01B_REQUIRED_OUTPUTS = (
    "manifest/runtime_manifest.json",
    "manifest/input_file_sha256.tsv",
    "data/growth_variable_identity_audit.tsv",
    "data/acetate_dual_role_audit.tsv",
    "data/canonical_component_alias_registry.tsv",
    "data/component_role_by_condition_audit.tsv",
    "data/cross_layer_join_identity_policy.tsv",
    "data/phase01a_policy_carry_forward_audit.tsv",
    "data/input_path_resolution_audit.tsv",
    "data/input_surface_availability_audit.tsv",
    "data/input_schema_inventory.tsv",
    "data/input_data_basis_policy_audit.tsv",
    "data/stat_pcmci_edge_long.tsv",
    "data/stat_pcmci_model_context_long.tsv",
    "data/stat_descriptive_node_state_long.tsv",
    "data/stat_interdependence_pair_window_long.tsv",
    "data/stat_conditioned_pair_global_long.tsv",
    "data/stat_dense_data_provenance_long.tsv",
    "data/kinetic_growth_primary_long.tsv",
    "data/kinetic_rate_primary_long.tsv",
    "data/kinetic_temporal_coupling_primary_long.tsv",
    "data/kinetic_yield_primary_long.tsv",
    "data/kinetic_disabled_branch_inventory.tsv",
    "data/kinetic_traceability_long.tsv",
    "data/input_join_key_audit.tsv",
    "data/many_to_many_origin_diagnostic.tsv",
    "data/per_surface_natural_key_profile.tsv",
    "data/candidate_key_uniqueness_profile.tsv",
    "data/lag_invariant_duplicate_origin_audit.tsv",
    "data/policy_surface_non_joinable_registry.tsv",
    "data/join_admissibility_contract.tsv",
    "data/phase02_join_contract.tsv",
    "data/input_empty_surface_audit.tsv",
    "audit/output_root_boundary_audit.tsv",
    "audit/repo_contamination_audit.tsv",
    "audit/phase01b_validation_summary.tsv",
)
PHASE01B_JOIN_REPAIR_REQUIRED_OUTPUTS = (
    "manifest/runtime_manifest.json",
    "data/input_join_key_audit_original.tsv",
    "data/input_join_key_audit.tsv",
    "data/many_to_many_origin_diagnostic.tsv",
    "data/per_surface_natural_key_profile.tsv",
    "data/candidate_key_uniqueness_profile.tsv",
    "data/lag_invariant_duplicate_origin_audit.tsv",
    "data/policy_surface_non_joinable_registry.tsv",
    "data/join_admissibility_contract.tsv",
    "data/phase02_join_contract.tsv",
    "audit/output_root_boundary_audit.tsv",
    "audit/repo_contamination_audit.tsv",
    "audit/many_to_many_root_cause_validation_summary.tsv",
)

STAT_RUN_REQUIRED_SURFACES = (
    "results/effects.tsv",
    "results/network_partialcorr.tsv",
    "results/interdependence_windows.tsv",
    "tables/snapshots.tsv",
    "tables/window_deltas.tsv",
    "intermediate/pcmci_dense_replicate_input.tsv",
    "intermediate/dense_series_interpolated.tsv",
    "intermediate/analysis_view_observed.tsv",
    "audit/pcmci_qc.json",
    "audit/partialcorr_qc.json",
    "audit/pcmci_dense_qc.json",
    "audit/postrun_statistical_audits.tsv",
    "audit/series_index.tsv",
    "audit/availability_matrix.tsv",
    "qc/schema_check.tsv",
    "manifest/run_manifest.json",
)

KINETIC_REAL_ONLY_REQUIRED_SURFACES = (
    "95_audit/growth_windows_handoff.tsv",
    "95_audit/metabolite_interval_rates_handoff.tsv",
    "95_audit/temporal_coupling_classification_handoff.tsv",
    "95_audit/yield_pairs_handoff.tsv",
    "95_audit/growth_window_audit.tsv",
    "95_audit/metabolite_rate_audit.tsv",
    "95_audit/kinetic_replicate_consensus_audit.tsv",
    "95_audit/yield_audit.tsv",
    "93_growth_windows/growth_source_audit.tsv",
)

KINETIC_REAL_ONLY_OPTIONAL_SURFACES = (
    "93_growth_windows/growth_windows_best.tsv",
    "94_accessible_kinetics/metabolite_interval_rates.tsv",
    "94_accessible_kinetics/partial_mass_balance.tsv",
    "94_accessible_kinetics/methodological_exclusions.tsv",
)

SCENARIO_ALIASES = {
    "MIX_MAX": "MIX_MAX",
    "Mix-max": "MIX_MAX",
    "MAX": "MAX",
    "Max concentration": "MAX",
    "MIN": "MIN",
    "Min concentration": "MIN",
}

MANUAL_POLICY_SURFACE = "SLL_CANONICAL_IDENTITY_POLICY_OD_ACETATE_v1.md"
