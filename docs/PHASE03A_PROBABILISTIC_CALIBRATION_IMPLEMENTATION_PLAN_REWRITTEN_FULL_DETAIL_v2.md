# PHASE03A_PROBABILISTIC_CALIBRATION_IMPLEMENTATION_PLAN_REWRITTEN_FULL_DETAIL_v2

## Controller

- Controller SHA: `334057762e47bc69e6e8d0b96a7a642bf204302a`
- Controlling Phase 02 runtime:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE02_RELATION_EVIDENCE_INTAKE_20260626_112045`
- Authorized repo root:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE`
- Authorized runtime output root:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS`

This repo-local controller file mirrors the accepted Phase03A contract used for implementation on 2026-06-26. Phase03A converts Phase 02 relation-evidence intake into internal non-causal posterior relation-support probabilities only.

## Scope

Phase03A must:

- add `phase03a`, not `phase03`
- consume only the approved Phase 02 runtime
- reject `--stat-root`, `--kin-root`, and `--phase01b-runtime`
- preserve `run_max_lag` and `edge_lag`
- keep `real_only` as the only kinetic branch
- produce posterior relation-support artifacts, manifests, audits, and validation

Phase03A must not:

- read raw statistical roots
- read raw kinetic roots
- reopen Phase01B runtimes directly
- generate QA22 outputs
- generate topology outputs
- generate human or technical reports
- generate final GO/NO-GO artifacts
- implement Phase03B

## Required Inputs

Phase03A reads only these Phase 02 surfaces:

- `manifest/runtime_manifest.json`
- `audit/phase02_validation_summary.tsv`
- `data/phase02_preflight_audit.tsv`
- `data/phase02_input_surface_manifest.tsv`
- `data/phase02_join_contract_consumption_audit.tsv`
- `data/relation_anchor_registry.tsv`
- `data/stat_temporal_pcmci_evidence_intake.tsv`
- `data/stat_descriptive_evidence_intake.tsv`
- `data/stat_interdependence_evidence_intake.tsv`
- `data/stat_conditioned_pair_evidence_intake.tsv`
- `data/kinetic_growth_evidence_intake.tsv`
- `data/kinetic_rate_evidence_intake.tsv`
- `data/kinetic_temporal_coupling_evidence_intake.tsv`
- `data/kinetic_yield_evidence_intake.tsv`
- `data/relation_evidence_tensor.tsv`
- `data/phase02_forbidden_output_scan.tsv`
- `data/phase02_empty_or_absent_evidence_audit.tsv`

## Runtime Outputs

Phase03A must write:

- `manifest/runtime_manifest.json`
- `data/phase03_input_runtime_manifest_audit.tsv`
- `data/phase03_input_surface_manifest.tsv`
- `data/phase03_preflight_audit.tsv`
- `data/probability_method_manifest.tsv`
- `data/probability_method_manifest.json`
- `data/temporal_pcmci_evidence_stat_surface.tsv`
- `data/temporal_pcmci_calibration_surface.tsv`
- `data/multilag_temporal_profile_surface.tsv`
- `data/conditioned_pair_probability_evidence_surface.tsv`
- `data/descriptive_probability_evidence_surface.tsv`
- `data/interdependence_probability_evidence_surface.tsv`
- `data/kinetic_likelihood_surface.tsv`
- `data/semantic_polarity_registry.tsv`
- `data/semantic_compatibility_surface.tsv`
- `data/relation_probability_evidence_tensor.tsv`
- `data/posterior_relation_state.tsv`
- `data/posterior_relation_state.json`
- `data/probability_calibration_audit.tsv`
- `data/probability_limitations_audit.tsv`
- `data/phase03_forbidden_output_scan.tsv`
- `data/phase03_empty_or_absent_probability_audit.tsv`
- `audit/output_root_boundary_audit.tsv`
- `audit/repo_contamination_audit.tsv`
- `audit/phase03_validation_summary.tsv`

## Posterior State Space

Allowed internal posterior states:

- `positive_support`
- `negative_support`
- `ambiguous_or_mixed`
- `insufficient_or_uninformative`

Required interpretation boundary:

- posterior probabilities are internal relation-support probabilities
- posterior probabilities are not causal probabilities
- posterior states are not QA states
- posterior states are not topology states
- posterior states are not final decision states

## Core Rules

- Temporal evidence statistic:
  `signed_evidence_score = sign(effect_value) * -log10(max(q_value, 1e-12))`
- Preferred calibration route: `empirical_rank_by_run_max_lag`
- Secondary route: `empirical_rank_pooled_lags`
- Conservative fallback: `conservative_logistic_fallback`
- Conditioned-pair evidence remains non-directional by itself
- Descriptive evidence remains contextual and conservative
- Interdependence evidence remains undirected
- Semantic compatibility can bonus or penalize but cannot flip temporal sign
- Final posterior is produced by temperature-controlled softmax across the four internal relation states

## Forbidden Outputs

Phase03A must not generate:

- `runtime_question_answer_matrix.tsv`
- `runtime_question_answer_matrix.json`
- `question_answer_evidence_trace.tsv`
- `network_topology_summary.tsv`
- `network_topology_summary.json`
- `final_static_release_decision.json`
- `final_machine_readable_consistency_audit.tsv`
- `TECHNICAL_QUESTION_ANSWER_REPORT_*.md`
- `HUMAN_REPORT_*.md`

## Validation Gates

`audit/phase03_validation_summary.tsv` must pass at least:

- `output_root_external_boundary`
- `repo_no_contamination`
- `manifest_phase03a_state`
- `phase02_runtime_manifest_valid`
- `phase02_validation_clean`
- `phase03a_required_inputs_present`
- `phase02_forbidden_outputs_absent`
- `relation_evidence_tensor_present`
- `relation_evidence_tensor_not_posterior`
- `no_raw_roots_consumed`
- `no_phase01b_runtime_direct_consumption`
- `run_max_lag_edge_lag_preserved`
- `no_global_lag_priority`
- `kinetic_real_only_only`
- `real_plus_interpolated_absent_from_kinetic_likelihood`
- `calibration_route_declared`
- `empirical_or_fallback_route_justified`
- `probability_method_manifest_exists`
- `semantic_polarity_registry_exists`
- `semantic_compatibility_surface_exists`
- `multilag_profile_preserved`
- `yield_absence_only_if_legitimate`
- `q_values_not_direct_probability`
- `posterior_state_columns_complete`
- `posterior_probabilities_between_zero_and_one`
- `posterior_probabilities_sum_to_one`
- `posterior_not_causal_probability`
- `posterior_not_qa_answer`
- `posterior_not_topology`
- `posterior_not_final_decision`
- `forbidden_outputs_absent`
- `required_artifacts_exist`
- `phase03a_status_complete_waiting_for_phase03b_plan`

Success requires `0` WARN/warning and `0` FAIL/error rows.

## Exact CLI Smoke

```text
python -m sll_probabilistic_pipeline.cli --phase phase03a --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --phase02-runtime "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE02_RELATION_EVIDENCE_INTAKE_20260626_112045" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
```

## Completion And Next Phase

Phase03A is complete only when the runtime decision is:

`PHASE03A_PROBABILISTIC_CALIBRATION_COMPLETE_WAITING_FOR_PHASE03B_PLAN`

The next allowed phase is planning only:

`PHASE03B_QA22_TOPOLOGY_AND_REPORTING_PLAN`
