# Phase 01B Join Root Cause Repair Completion Audit

Evidence snapshot date: `2026-06-24`

Note: later reruns under `PREDICTOR RESULTADOS` may create newer timestamped runtimes. This audit records one fully verified snapshot and remains valid as long as those referenced runtimes remain present.

Verified runtimes:

- Phase 01B rebuilt runtime:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_145643`
- Join-repair runtime:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260624_145522`

Validation commands executed:

```text
python -m py_compile <all project python files>
python -m pytest -q
python -m sll_probabilistic_pipeline.cli --phase phase01b --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --stat-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816" --kin-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
python -m sll_probabilistic_pipeline.cli --phase phase01b_join_repair --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --phase01b-runtime "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_093603" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
```

Observed command outcomes:

- `py_compile`: PASS
- `pytest -q`: PASS (`35` tests)
- `phase01b` CLI smoke: PASS
- `phase01b_join_repair` CLI smoke: PASS, final decision `PHASE02_PLAN_ALLOWED`

## Requirement Audit

| Plan requirement | Evidence | Status |
| --- | --- | --- |
| Add CLI phase `phase01b_join_repair` | `sll_probabilistic_pipeline/cli.py`, `sll_probabilistic_pipeline/config.py` | PASS |
| Require `--phase01b-runtime` only for repair phase | `sll_probabilistic_pipeline/cli.py` argument gating | PASS |
| Keep `--stat-root` and `--kin-root` required only for `phase01a` and `phase01b` | `sll_probabilistic_pipeline/cli.py` phase branching | PASS |
| Reject any repair `--out-root` inside the repository | `sll_probabilistic_pipeline/paths.py`, `tests/test_path_resolution.py` | PASS |
| Create repair runtime under external results root | `sll_probabilistic_pipeline/paths.py`, `tests/test_path_resolution.py`, repair runtime path above | PASS |
| Reject a `phase01b-runtime` outside the allowed external results root | `tests/test_phase01b_join_repair_preflight.py` | PASS |
| Reject disallowed warning rows during repair preflight | `tests/test_phase01b_join_repair_preflight.py` | PASS |
| Reject error-level Phase 01B validation failures during repair preflight | `tests/test_phase01b_join_repair_preflight.py` | PASS |
| Read only Phase 01B normalized outputs plus Phase 01A carry-forward artifacts | `sll_probabilistic_pipeline/phase01b_join_repair.py` loads only `phase01b_runtime/data/*.tsv` and `phase01a` carry-forward surfaces | PASS |
| Refactor join profiling into shared resolver used by future `phase01b` and repair phase | `sll_probabilistic_pipeline/standardize/joins.py`, `sll_probabilistic_pipeline/phase01b.py`, `sll_probabilistic_pipeline/phase01b_join_repair.py` | PASS |
| Preserve broad-key risk profile while adding natural-key resolution fields | `data/input_join_key_audit.tsv` in both rebuilt Phase 01B and repair runtimes | PASS |
| Extend join audit with `left_row_count`, `right_row_count`, `left_max_multiplicity`, `right_max_multiplicity`, `max_cartesian_expansion`, `missing_key_dimensions`, `duplicate_origin`, `join_admissibility`, `resolution_state` | `data/input_join_key_audit.tsv` in rebuilt Phase 01B and repair runtimes | PASS |
| Resolve `stat_descriptive_node_state_long.tsv -> kinetic_rate_primary_long.tsv` as `projection_only` | `data/input_join_key_audit.tsv`, `data/join_admissibility_contract.tsv`, `tests/test_join_admissibility_contract.py` | PASS |
| Resolve `stat_descriptive_node_state_long.tsv -> kinetic_temporal_coupling_primary_long.tsv` as `projection_only` | `data/input_join_key_audit.tsv`, `data/join_admissibility_contract.tsv`, `tests/test_join_admissibility_contract.py` | PASS |
| Resolve `growth_variable_identity_audit.tsv -> kinetic_growth_primary_long.tsv` as `policy_lookup_only` | `data/input_join_key_audit.tsv`, `data/join_admissibility_contract.tsv`, `tests/test_join_admissibility_contract.py` | PASS |
| Register growth identity as `non_joinable_as_measurement` | `data/policy_surface_non_joinable_registry.tsv`, `tests/test_policy_surface_non_joinable_registry.py` | PASS |
| Diagnose descriptive many-to-many origin as omitted dimensions plus lag-invariant duplication | `data/many_to_many_origin_diagnostic.tsv`, `data/lag_invariant_duplicate_origin_audit.tsv`, `tests/test_many_to_many_origin_profiles.py` | PASS |
| Preserve measured cartesian exposure `1008` for descriptive broad-key joins | `data/many_to_many_origin_diagnostic.tsv`, `tests/test_many_to_many_origin_profiles.py` | PASS |
| Preserve measured cartesian exposure `21648` for growth policy misuse | `data/many_to_many_origin_diagnostic.tsv`, `tests/test_many_to_many_origin_profiles.py` | PASS |
| Backport repair semantics into future `phase01b` so unresolved risk is not accepted as `WARN` | `sll_probabilistic_pipeline/validation/phase01b.py`, rebuilt Phase 01B validation summary | PASS |
| Rebuilt `phase01b` validation contains zero `WARN/warning` rows | `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_145643\audit\phase01b_validation_summary.tsv` | PASS |
| Produce repair runtime outputs `input_join_key_audit_original.tsv`, repaired `input_join_key_audit.tsv`, diagnostics, contracts, validation summary, manifest | repair runtime output inventory | PASS |
| Repair validation summary contains only `PASS/info` rows | `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260624_145522\audit\many_to_many_root_cause_validation_summary.tsv` | PASS |
| No active `WARN/warning` rows remain in repair runtime | same validation summary as above | PASS |
| No `FAIL/error` rows remain in repair runtime | same validation summary as above | PASS |
| Final repair decision is explicit and machine-readable | repair runtime `manifest/runtime_manifest.json` contains `phase02_plan_decision=PHASE02_PLAN_ALLOWED` | PASS |
| No Phase 02 artifacts are generated by the repair phase | repair validation summary check `no_phase02_artifacts_generated=PASS` | PASS |
| Add tests for admissibility, origin profiling, non-joinable registry, repair smoke | `tests/test_join_admissibility_contract.py`, `tests/test_many_to_many_origin_profiles.py`, `tests/test_policy_surface_non_joinable_registry.py`, `tests/test_phase01b_join_repair_smoke.py` | PASS |
| Add tests for repair preflight boundary and validation rejection rules | `tests/test_phase01b_join_repair_preflight.py` | PASS |
| Keep AGENTS CLI guidance aligned with the new checkpoint | `AGENTS.md` updated validation command block | PASS |

## Runtime Evidence Summary

Rebuilt Phase 01B runtime evidence:

- Manifest:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_145643\manifest\runtime_manifest.json`
- Validation:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_145643\audit\phase01b_validation_summary.tsv`
- Join-risk check result:
  `join_many_to_many_risk_profiled_not_joined = PASS`
- Warning rows:
  `0`

Repair runtime evidence:

- Manifest:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260624_145522\manifest\runtime_manifest.json`
- Validation:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260624_145522\audit\many_to_many_root_cause_validation_summary.tsv`
- Final decision:
  `PHASE02_PLAN_ALLOWED`
- Warning rows:
  `0`
- Fail/error rows:
  `0`

## Conclusion

The implemented state satisfies the explicit objectives of the Phase 01B Join-Root-Cause Repair Plan and the documentary evidence above is sufficient to verify completion:

- the root cause of each many-to-many risk row is explained;
- each problematic pair is reclassified into an explicit admissibility mode;
- Phase 01B no longer tolerates unresolved join risk as a warning;
- the repair runtime is clean and machine-readable;
- the final state is `PHASE02_PLAN_ALLOWED`.
