# SLL — Probabilistic calculation contract v1

## 1. Purpose

This document defines the calculation that Codex must implement in Python. The model is not a subjective score and must not claim final causality.

## 2. Unit of calculation

The primary relation is:

```text
r = target ← perturbator | scenario | condition_id | replicate | window | run_max_lag | edge_lag
```

When a layer does not contain all fields, the pipeline must keep nulls explicit and audit the missing dimension.

## 3. Relational states

Minimum states:

```text
no_internal_signal
positive_temporal_support
negative_temporal_support
basal_axis_compatible
perturbation_reconfiguration
growth_associated_support
conditioned_pair_only
kinetic_support_only
contextual_only
external_validation_required
internal_failure_localized
```

## 4. Core model

For each relation `r` and state `h`:

```text
log_support(r,h) =
    log_prior(h)
  + logLR_descriptive(r,h)
  + logLR_conditioned_pair(r,h)
  + logLR_PCMCI_LAG01(r,h)
  + logLR_PCMCI_LAG02(r,h)
  + logLR_PCMCI_LAG03(r,h)
  + logLR_PCMCI_LAG04(r,h)
  + logLR_kinetic(r,h)
  + logLR_semantic(r,h)
  + logLR_QC(r,h)
```

Then:

```text
P(H_r=h | E_r) = softmax_h(log_support(r,h))
```

This is posterior support/compatibility probability for internal evidence states, not causal probability.

## 5. Statistical calibration

### 5.1 PCMCI evidence statistic

For every edge and lag:

```text
x_pcmci(r,l) = sign(effect_value) * -log10(max(q_value, q_floor))
```

`x_pcmci` is an evidence statistic, not a probability.

### 5.2 Preferred probability of signal

Use empirical-null/local-FDR calibration when the data volume allows:

```text
local_fdr_l(x) = pi0_l * f0_l(x) / f_l(x)
P_signal_pcmci_l(x) = 1 - local_fdr_l(x)
```

Build calibration separately by `edge_lag` and, if justified by sample size, by variable family or condition class.

### 5.3 Fallback calibration

If empirical-null calibration is not stable, use conservative Bayes-factor or p/q-value calibration and write:

```text
bayes_factor_calibration_audit.tsv
```

The audit must state that the fallback is conservative and not a causal probability.

## 6. Multilag rules

Do not pick a global winner lag.

Required relation-level lag fields:

```text
P_signal_LAG01
P_signal_LAG02
P_signal_LAG03
P_signal_LAG04
sign_LAG01
sign_LAG02
sign_LAG03
sign_LAG04
P_fast
P_intermediate
P_late
P_persistent
P_conflict
lag_dominant_local
lag_distribution_entropy
```

`lag_dominant_local` is allowed only as `argmax(P_signal_LAGXX)` and must never hide the full distribution.

## 7. Conditioned-pair evidence

Partial correlation / graphical structure supports conditioned pair dependence. It does not provide direction.

Required fields:

```text
P_conditioned_pair_signal
conditioned_pair_sign
conditioned_pair_strength
conditioned_pair_role = pair_support_only | supports_temporal_edge | conflicts_temporal_edge | absent
```

## 8. Descriptive evidence

Descriptive surfaces support target state, direction of change, and visibility by window. They do not invent perturbators.

Required fields:

```text
P_descriptive_target_change
P_descriptive_window_support
descriptive_direction
descriptive_consistency
```

## 9. Kinetic likelihood

Kinetic evidence must use `real_only` data only.

Required fields:

```text
P_kinetic_support
kinetic_role = growth | metabolite_rate | temporal_coupling | yield | absence | excluded
kinetic_direction
kinetic_rate_strength
kinetic_consensus
kinetic_audit_status
```

`real_plus_interpolated` must never contribute to `P_kinetic_support`.

## 10. Semantic compatibility

The semantic layer maps signs to biological interpretation. It prevents treating positive/negative signs as automatic promotion/inhibition.

Examples:

```text
succinate increase may support product formation
fumarate decrease may support acceptor consumption
lnOD increase may support growth
inhibitor decrease may support degradation/consumption
acetate increase may be accumulation, production, or decoupling, not automatic promotion
```

Required output:

```text
semantic_compatibility_audit.tsv
```

## 11. Required probabilistic outputs

```text
relation_evidence_tensor.tsv
empirical_null_calibration_summary.tsv
local_fdr_signal_probability.tsv
bayes_factor_calibration_audit.tsv
pcmci_lag_specific_evidence.tsv
pcmci_lag_persistence_surface.tsv
pcmci_lag_conflict_audit.tsv
kinetic_likelihood_surface.tsv
conditioned_pair_probability_surface.tsv
descriptive_probability_surface.tsv
posterior_relation_state.tsv
posterior_relation_state.json
score_global_local_surface.tsv
probabilistic_model_audit.json
```

## 12. Score policy

A score may be derived for ranking, but it must be downstream of posterior probabilities and never treated as causal probability.

Required score fields:

```text
posterior_primary_state
posterior_primary_probability
ranking_score
ranking_scope = local | global
ranking_reason
not_causal_probability_yes_no = yes
```
