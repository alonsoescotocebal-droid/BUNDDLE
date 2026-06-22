# SLL — Acceptance tests and done definition v1

## 1. Done is artifact-based

Codex may not declare completion because a report looks plausible. Completion requires direct artifacts and validation.

## 2. Mandatory tests

At minimum:

```bash
python -m py_compile $(git ls-files '*.py')
python -m pytest -q
```

If shell expansion is not available on Windows, use a small Python script to compile all tracked `.py` files.

## 3. Mandatory runtime validation

The runtime validator must check:

```text
- all mandatory input-reader outputs exist
- statistical layer retains interpolation/provenance fields
- kinetic support uses real_only only
- real_plus_interpolated is inventoried as disabled if present
- run_max_lag and edge_lag are both present
- no global lag priority is used
- all four lag probability fields are present
- posterior probabilities sum to approximately 1 per relation where applicable
- 22 QA rows exist
- every QA row has valid answer_state
- no QA row uses narrative-only closure
- final JSON/TSV/Markdown decisions agree
```

## 4. Mandatory final files

```text
data/input_path_resolution_audit.tsv
data/input_surface_availability_audit.tsv
data/input_schema_inventory.tsv
data/input_data_basis_policy_audit.tsv
data/stat_pcmci_edge_long.tsv
data/kinetic_growth_primary_long.tsv
data/kinetic_rate_primary_long.tsv
data/kinetic_temporal_coupling_primary_long.tsv
data/kinetic_disabled_branch_inventory.tsv
data/relation_evidence_tensor.tsv
data/pcmci_lag_specific_evidence.tsv
data/kinetic_likelihood_surface.tsv
data/posterior_relation_state.tsv
data/posterior_relation_state.json
data/probabilistic_question_answer_matrix.tsv
data/probabilistic_question_answer_matrix.json
data/probabilistic_question_answer_evidence_trace.tsv
data/network_topology_summary.tsv
data/network_topology_summary.json
data/final_machine_readable_consistency_audit.tsv
data/final_static_release_decision.json
report/TECHNICAL_PROBABILISTIC_QA_REPORT_<STAMP>.md
report/HUMAN_PROBABILISTIC_REPORT_<STAMP>.md
manifest/runtime_manifest.json
```

## 5. NO-GO triggers

Final decision must be `NO-GO` if:

```text
- any mandatory surface is missing without legitimate absence audit
- any kinetic likelihood uses real_plus_interpolated
- any relation treats q_value or p_value as causal probability
- any single lag is hardcoded as priority
- any question has internal_failure_localized
- evidence trace is missing for answered_defensible rows
- raw input files are changed
```
