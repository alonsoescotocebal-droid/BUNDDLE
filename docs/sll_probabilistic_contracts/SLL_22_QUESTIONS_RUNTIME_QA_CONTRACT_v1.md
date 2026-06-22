# SLL — Contract for the 22 calculated questions v1

## 1. Purpose

The 22 questions are no longer narrative prompts. They are runtime-calculated outputs produced from probabilistic and audit surfaces.

Every question row must contain:

```text
question_id
question_text
answer_state
primary_surface
primary_row_key
supporting_surfaces
direct_read_yes_no
inference_used_yes_no
posterior_fields_used
trace_id
failure_boundary_if_any
```

Allowed states:

```text
answered_defensible
answered_exploratory_with_caution
legitimate_absence_demonstrated
external_validation_required
internal_failure_localized
```

## 2. Question-to-calculation map

| Q | Runtime calculation | Required source surface |
|---|---|---|
| Q01 | observed node eligibility and semantic role | system_observed_node_registry.tsv |
| Q02 | OD600 and non-metabolite inclusion as general observed-node rule | system_observed_node_registry.tsv; semantic_compatibility_audit.tsv |
| Q03 | MIX_MAX `target ← perturbator` posterior relations | posterior_relation_state.tsv |
| Q04 | positive support relations in MIX_MAX | posterior_relation_state.tsv; pcmci_lag_specific_evidence.tsv; kinetic_likelihood_surface.tsv |
| Q05 | negative/brake/deviation support in MIX_MAX | posterior_relation_state.tsv; semantic_compatibility_audit.tsv |
| Q06 | local/global ranking score derived from posterior | score_global_local_surface.tsv |
| Q07 | calibrated statistical support | local_fdr_signal_probability.tsv; conditioned_pair_probability_surface.tsv; descriptive_probability_surface.tsv |
| Q08 | temporal support by all lags | pcmci_lag_specific_evidence.tsv |
| Q09 | kinetic support from real_only only | kinetic_likelihood_surface.tsv |
| Q10 | local dominant lag and full distribution | pcmci_lag_specific_evidence.tsv |
| Q11 | fast/intermediate/late/persistent/conflict class | pcmci_lag_persistence_surface.tsv; pcmci_lag_conflict_audit.tsv |
| Q12 | conditioned pairs and their destinations | pair_conditioned_signal_flow_audit.tsv |
| Q13 | actionable/candidate/contextual class | intervention_priority_surface.tsv |
| Q14 | review priority | intervention_priority_surface.tsv |
| Q15 | validation priority | intervention_priority_surface.tsv |
| Q16 | intervention candidates with caution | intervention_priority_surface.tsv |
| Q17 | main perturbators by weighted out-degree | network_topology_summary.tsv/json |
| Q18 | sensitive targets by weighted in-degree | network_topology_summary.tsv/json |
| Q19 | network topology class | network_topology_summary.tsv/json |
| Q20 | unanswered or blocked questions and exact boundary | probabilistic_question_answer_matrix.tsv |
| Q21 | final documentary consistency | final_machine_readable_consistency_audit.tsv |
| Q22 | GO/NO-GO final decision | final_static_release_decision.json |

## 3. Mandatory QA outputs

```text
probabilistic_question_answer_matrix.tsv
probabilistic_question_answer_matrix.json
probabilistic_question_answer_evidence_trace.tsv
question_answer_surface_coverage_audit.tsv
question_answer_failure_boundary_audit.tsv
```

## 4. Closure rule

A human report cannot close a question by itself. A question closes only if its machine-readable row has valid state, source surface, source row key, trace ID, and no contradiction with final audit JSON/TSV.

If any question has `internal_failure_localized`, final decision must be `NO-GO`.
