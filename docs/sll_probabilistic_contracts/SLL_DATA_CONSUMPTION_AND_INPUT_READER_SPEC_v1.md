# SLL — Data consumption and input reader specification v1

## 1. Purpose

Define exactly how the Python program must consume SLL statistical and kinetic folders before any probabilistic calculation.

## 2. Canonical input folders

The pipeline receives two explicit roots:

```text
--stat-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816"
--kin-root  "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037"
```

It may also receive parents:

```text
--stat-parent "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs"
--kin-parent  "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations"
```

If exact roots are absent, the resolver may scan the parent folders for candidates, but must not silently substitute paths. It must write:

```text
input_path_resolution_audit.tsv
```

with at least:

```text
requested_role, requested_path, resolved_path, exists_yes_no, candidate_count, selected_yes_no, deviation_reason, decision
```

## 3. Statistical input contract

### 3.1 Accepted statistical run structure

Expected parent run:

```text
SLL_REAL_PCMCI_LAG01-04_20260401_174816
```

Expected internal run folders:

```text
SLL_REAL_PCMCI_LAG01_*
SLL_REAL_PCMCI_LAG02_*
SLL_REAL_PCMCI_LAG03_*
SLL_REAL_PCMCI_LAG04_*
```

Each run folder represents a PCMCI run with a different maximum lag. It does not represent a single edge lag.

Mandatory distinction:

```text
run_max_lag = parsed from folder name LAG01, LAG02, LAG03, LAG04
edge_lag    = read from results/effects.tsv column `lag`
```

Never collapse these fields.

### 3.2 Statistical surfaces to read

Minimum surfaces:

```text
results/effects.tsv
results/network_partialcorr.tsv
results/interdependence_windows.tsv
tables/snapshots.tsv
tables/window_deltas.tsv
intermediate/pcmci_dense_replicate_input.tsv
intermediate/dense_series_interpolated.tsv
intermediate/analysis_view_observed.tsv
audit/pcmci_qc.json
audit/partialcorr_qc.json
audit/pcmci_dense_qc.json
audit/postrun_statistical_audits.tsv
audit/series_index.tsv
audit/availability_matrix.tsv
qc/schema_check.tsv
manifest/run_manifest.json
```

If a surface is missing, record it in:

```text
input_surface_availability_audit.tsv
```

Do not infer a replacement unless the contract explicitly declares an alias.

### 3.3 Statistical data basis

The statistical layer is allowed to consume audited interpolated/dense data because PCMCI, partial correlation, interdependence windows, and temporal descriptions require sufficient regularity and temporal coverage.

This is not a disconnection from real data. Real observations are the experimental anchor and interpolation audit base.

Prohibited:

```text
- treating interpolated values as new experimental measurements
- hiding interpolation flags
- using interpolation without audit status
- preferring a single lag globally
```

## 4. Kinetic input contract

### 4.1 Accepted kinetic run structure

Expected kinetic root:

```text
SLL_rates_block_20260426_133037
```

Expected branches:

```text
SLL_20260426_133037_real_only
SLL_20260426_133037_real_plus_interpolated
```

Only this branch is enabled:

```text
SLL_20260426_133037_real_only
```

This branch is disabled by canonical rule:

```text
SLL_20260426_133037_real_plus_interpolated
```

The disabled branch may be inventoried but cannot support kinetic likelihood, sensitivity, complementarity, validation, or intervention priority.

### 4.2 Kinetic surfaces to read from `real_only`

Minimum primary handoff surfaces:

```text
95_audit/growth_windows_handoff.tsv
95_audit/metabolite_interval_rates_handoff.tsv
95_audit/temporal_coupling_classification_handoff.tsv
95_audit/yield_pairs_handoff.tsv
95_audit/growth_window_audit.tsv
95_audit/metabolite_rate_audit.tsv
95_audit/kinetic_replicate_consensus_audit.tsv
95_audit/yield_audit.tsv
```

Supporting surfaces:

```text
93_growth_windows/growth_windows_best.tsv
94_accessible_kinetics/metabolite_interval_rates.tsv
94_accessible_kinetics/partial_mass_balance.tsv
94_accessible_kinetics/methodological_exclusions.tsv
report_contract_summary.json
report_contract_metrics.tsv
report_output_catalog.tsv
```

## 5. Required normalized outputs from the input reader

Before any probability calculation, generate:

```text
input_bundle_manifest.tsv
input_path_resolution_audit.tsv
input_surface_availability_audit.tsv
input_schema_inventory.tsv
canonical_alias_registry.tsv
input_data_basis_policy_audit.tsv
stat_pcmci_edge_long.tsv
stat_pcmci_model_context_long.tsv
stat_descriptive_node_state_long.tsv
stat_interdependence_pair_window_long.tsv
stat_conditioned_pair_global_long.tsv
stat_dense_data_provenance_long.tsv
kinetic_growth_primary_long.tsv
kinetic_rate_primary_long.tsv
kinetic_temporal_coupling_primary_long.tsv
kinetic_yield_primary_long.tsv
kinetic_disabled_branch_inventory.tsv
kinetic_traceability_long.tsv
input_join_key_audit.tsv
input_empty_surface_audit.tsv
```

## 6. Join policy

Before joining statistical and kinetic layers, compute:

```text
candidate_keys
normalized_keys
null_rate_by_key
unique_key_rate
many_to_many_risk
match_rate
unmatched_left_count
unmatched_right_count
```

No probabilistic join is allowed without `input_join_key_audit.tsv`.

## 7. Failure behavior

A missing or empty surface must become one of:

```text
available
missing_optional
missing_required_internal_failure
empty_legitimate
empty_requires_audit
excluded_by_canonical_rule
```

Silent omission is forbidden.
