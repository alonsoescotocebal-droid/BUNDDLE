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
DEFAULT_PHASE01B_REBUILT_RUNTIME = DEFAULT_RESULTS_ROOT / "SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628"
DEFAULT_PHASE02_REBUILT_RUNTIME = DEFAULT_RESULTS_ROOT / "SLL_PHASE02_RELATION_EVIDENCE_INTAKE_20260626_112045"

SUPPORTED_PHASES = {"phase01a", "phase01b", "phase01b_join_repair", "phase02", "phase03a"}
PHASE01B_RUNTIME_PREFIX = "SLL_PHASE01B_NORMALIZED_INPUT_READER_"
PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX = "SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_"
PHASE01B_REPO_OUTPUT_REJECTION_CODE = "PHASE01B_OUTPUT_ROOT_INSIDE_REPO_FORBIDDEN"
PHASE02_RUNTIME_PREFIX = "SLL_PHASE02_RELATION_EVIDENCE_INTAKE_"
PHASE02_REPO_OUTPUT_REJECTION_CODE = "PHASE02_OUTPUT_ROOT_INSIDE_REPO_FORBIDDEN"
PHASE02_CONTROLLER_SHA = "b3a3299164318ef71885ed6d1f801b4aef96b53e"
PHASE02_APPROVED_COMPLETION_STATE = "PHASE02_RELATION_EVIDENCE_INTAKE_COMPLETE_WAITING_FOR_PHASE03_PLAN"
PHASE02_BLOCKED_STATE = "PHASE02_RELATION_EVIDENCE_INTAKE_BLOCKED"
PHASE03A_RUNTIME_PREFIX = "SLL_PHASE03A_PROBABILISTIC_CALIBRATION_"
PHASE03A_REPO_OUTPUT_REJECTION_CODE = "PHASE03A_OUTPUT_ROOT_INSIDE_REPO_FORBIDDEN"
PHASE03A_CONTROLLER_SHA = "334057762e47bc69e6e8d0b96a7a642bf204302a"
PHASE03A_APPROVED_COMPLETION_STATE = "PHASE03A_PROBABILISTIC_CALIBRATION_COMPLETE_WAITING_FOR_PHASE03B_PLAN"
PHASE03A_BLOCKED_STATE = "PHASE03A_PROBABILISTIC_CALIBRATION_BLOCKED"

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
PHASE02_REQUIRED_INPUTS = (
    "manifest/runtime_manifest.json",
    "audit/phase01b_validation_summary.tsv",
    "data/input_path_resolution_audit.tsv",
    "data/input_surface_availability_audit.tsv",
    "data/input_schema_inventory.tsv",
    "data/input_data_basis_policy_audit.tsv",
    "data/growth_variable_identity_audit.tsv",
    "data/acetate_dual_role_audit.tsv",
    "data/canonical_component_alias_registry.tsv",
    "data/component_role_by_condition_audit.tsv",
    "data/cross_layer_join_identity_policy.tsv",
    "data/phase01a_policy_carry_forward_audit.tsv",
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
)
PHASE02_REQUIRED_OUTPUTS = (
    "manifest/runtime_manifest.json",
    "data/phase02_input_runtime_manifest_audit.tsv",
    "data/phase02_input_surface_manifest.tsv",
    "data/phase02_preflight_audit.tsv",
    "data/relation_anchor_registry.tsv",
    "data/stat_temporal_pcmci_evidence_intake.tsv",
    "data/stat_descriptive_evidence_intake.tsv",
    "data/stat_interdependence_evidence_intake.tsv",
    "data/stat_conditioned_pair_evidence_intake.tsv",
    "data/kinetic_growth_evidence_intake.tsv",
    "data/kinetic_rate_evidence_intake.tsv",
    "data/kinetic_temporal_coupling_evidence_intake.tsv",
    "data/kinetic_yield_evidence_intake.tsv",
    "data/phase02_join_contract_consumption_audit.tsv",
    "data/relation_evidence_tensor.tsv",
    "data/phase02_forbidden_output_scan.tsv",
    "data/phase02_empty_or_absent_evidence_audit.tsv",
    "audit/output_root_boundary_audit.tsv",
    "audit/repo_contamination_audit.tsv",
    "audit/phase02_validation_summary.tsv",
)
PHASE02_FORBIDDEN_OUTPUTS = (
    "data/posterior_relation_state.tsv",
    "data/posterior_relation_state.json",
    "data/runtime_question_answer_matrix.tsv",
    "data/runtime_question_answer_matrix.json",
    "data/question_answer_evidence_trace.tsv",
    "data/network_topology_summary.tsv",
    "data/network_topology_summary.json",
    "data/final_static_release_decision.json",
    "data/final_machine_readable_consistency_audit.tsv",
)
PHASE03A_REQUIRED_INPUTS = (
    "manifest/runtime_manifest.json",
    "audit/phase02_validation_summary.tsv",
    "data/phase02_preflight_audit.tsv",
    "data/phase02_input_surface_manifest.tsv",
    "data/phase02_join_contract_consumption_audit.tsv",
    "data/relation_anchor_registry.tsv",
    "data/stat_temporal_pcmci_evidence_intake.tsv",
    "data/stat_descriptive_evidence_intake.tsv",
    "data/stat_interdependence_evidence_intake.tsv",
    "data/stat_conditioned_pair_evidence_intake.tsv",
    "data/kinetic_growth_evidence_intake.tsv",
    "data/kinetic_rate_evidence_intake.tsv",
    "data/kinetic_temporal_coupling_evidence_intake.tsv",
    "data/kinetic_yield_evidence_intake.tsv",
    "data/relation_evidence_tensor.tsv",
    "data/phase02_forbidden_output_scan.tsv",
    "data/phase02_empty_or_absent_evidence_audit.tsv",
)
PHASE03A_REQUIRED_OUTPUTS = (
    "manifest/runtime_manifest.json",
    "data/phase03_input_runtime_manifest_audit.tsv",
    "data/phase03_input_surface_manifest.tsv",
    "data/phase03_preflight_audit.tsv",
    "data/probability_method_manifest.tsv",
    "data/probability_method_manifest.json",
    "data/temporal_pcmci_evidence_stat_surface.tsv",
    "data/temporal_pcmci_calibration_surface.tsv",
    "data/multilag_temporal_profile_surface.tsv",
    "data/conditioned_pair_probability_evidence_surface.tsv",
    "data/descriptive_probability_evidence_surface.tsv",
    "data/interdependence_probability_evidence_surface.tsv",
    "data/kinetic_likelihood_surface.tsv",
    "data/semantic_polarity_registry.tsv",
    "data/semantic_compatibility_surface.tsv",
    "data/relation_probability_evidence_tensor.tsv",
    "data/posterior_relation_state.tsv",
    "data/posterior_relation_state.json",
    "data/probability_calibration_audit.tsv",
    "data/probability_limitations_audit.tsv",
    "data/phase03_forbidden_output_scan.tsv",
    "data/phase03_empty_or_absent_probability_audit.tsv",
    "audit/output_root_boundary_audit.tsv",
    "audit/repo_contamination_audit.tsv",
    "audit/phase03_validation_summary.tsv",
)
PHASE03A_FORBIDDEN_OUTPUTS = (
    "data/runtime_question_answer_matrix.tsv",
    "data/runtime_question_answer_matrix.json",
    "data/question_answer_evidence_trace.tsv",
    "data/network_topology_summary.tsv",
    "data/network_topology_summary.json",
    "data/final_static_release_decision.json",
    "data/final_machine_readable_consistency_audit.tsv",
    "report/TECHNICAL_QUESTION_ANSWER_REPORT_*.md",
    "report/HUMAN_REPORT_*.md",
)
PHASE03A_FORBIDDEN_INPUT_PATH_MARKERS = (
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs",
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations",
    "SLL_PHASE01B_",
)
PHASE03A_FORBIDDEN_POSTERIOR_SOURCE_COLUMNS = (
    "posterior_probability",
    "P_signal",
    "P_state",
    "causal_probability",
    "final_score",
    "qa_answer_state",
    "network_degree",
    "final_go_no_go",
    "p_positive_support",
    "p_negative_support",
    "p_ambiguous_or_mixed",
    "p_insufficient_or_uninformative",
    "posterior_state_argmax",
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
