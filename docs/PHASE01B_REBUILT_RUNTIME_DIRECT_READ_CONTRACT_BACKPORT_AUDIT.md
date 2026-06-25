# PHASE01B Rebuilt Runtime Direct-Read Contract Backport Audit

Evidence date: `2026-06-25`

## Summary

This corrective implementation backports the join-resolution direct-read contract into rebuilt `phase01b` runtimes so the Phase 02 readiness gate no longer depends on repair-only artifacts.

Final readiness decision:

```text
PHASE02_PLAN_ALLOWED_AFTER_REBUILT_RUNTIME_DIRECT_READ
```

This run does not implement Phase 02, does not add `phase02.py`, and does not generate posterior, QA22, topology, report, or Phase 02 runtime artifacts.

## Repository state

- Base SHA at implementation start:
  `97d343ddb75f34a419a15be234e56c23046e1871`
- Final HEAD SHA after implementation and verification:
  `97d343ddb75f34a419a15be234e56c23046e1871`
- Note:
  No commit was created in this checkpoint. The verified implementation exists as worktree changes on top of the same HEAD SHA.

## Files changed

- `sll_probabilistic_pipeline/config.py`
- `sll_probabilistic_pipeline/phase01b.py`
- `sll_probabilistic_pipeline/phase01b_join_repair.py`
- `sll_probabilistic_pipeline/standardize/joins.py`
- `sll_probabilistic_pipeline/validation/phase01b.py`
- `tests/_runtime_fixture.py`
- `tests/test_path_resolution.py`
- `tests/test_phase01b_direct_read_contract.py`
- `tests/test_phase01b_join_repair_preflight.py`
- `tests/test_phase01b_join_repair_smoke.py`
- `tests/test_phase01b_smoke.py`
- `docs/PHASE01B_REBUILT_RUNTIME_DIRECT_READ_CONTRACT_BACKPORT_AUDIT.md`

## Commands run

```text
python -m py_compile <all project python files>
python -m pytest -q
python -m sll_probabilistic_pipeline.cli --phase phase01b --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --stat-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816" --kin-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
python -m sll_probabilistic_pipeline.cli --phase phase01b_join_repair --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --phase01b-runtime "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
```

Observed results:

- `py_compile`: PASS (`42` Python files)
- `pytest -q`: PASS (`43` tests)
- `phase01b` CLI smoke: PASS
- `phase01b_join_repair` CLI smoke against the new rebuilt runtime: PASS

## Runtime paths generated

- Rebuilt `phase01b` runtime:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628`
- Join-repair runtime generated against the new rebuilt runtime:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260625_094715`

## Rebuilt runtime direct-read status

Required rebuilt-runtime files:

| Relative path | Direct-read status | Row count / note |
| --- | --- | --- |
| `manifest/runtime_manifest.json` | `present` | `phase=phase01b`, `outputs=36` |
| `audit/phase01b_validation_summary.tsv` | `present` | `1614` rows |
| `data/input_join_key_audit.tsv` | `present` | `4` rows |
| `data/join_admissibility_contract.tsv` | `present` | `3` rows |
| `data/many_to_many_origin_diagnostic.tsv` | `present` | `3` rows |
| `data/policy_surface_non_joinable_registry.tsv` | `present` | `1` row |
| `data/lag_invariant_duplicate_origin_audit.tsv` | `present` | `1064` rows |
| `data/phase02_join_contract.tsv` | `present` | `3` rows |

Additional join-resolution runtime files written directly by the rebuilt runtime:

| Relative path | Direct-read status | Row count |
| --- | --- | --- |
| `data/per_surface_natural_key_profile.tsv` | `present` | `5` rows |
| `data/candidate_key_uniqueness_profile.tsv` | `present` | `12` rows |

## Validation and gate status

Rebuilt `phase01b` validation summary:

- `WARN/warning` rows: `0`
- `FAIL/error` rows: `0`
- `repo_no_contamination`: `PASS`
- `no_phase02_outputs_present`: `PASS`
- `required_artifacts_exist`: `PASS`
- `join_admissibility_contract_complete`: `PASS`
- `phase02_join_contract_ready`: `PASS`

Join-repair validation summary against the rebuilt runtime:

- `phase02_plan_decision`: `PHASE02_PLAN_ALLOWED`
- `input_phase01b_warning_rows`: `0`
- `WARN/warning` rows: `0`
- `FAIL/error` rows: `0`

## Outcome

The rebuilt `phase01b` runtime now directly exposes the join-resolution artifacts that were previously available only in join-repair runtimes. The direct-read gate that blocked Phase 02 planning because of missing rebuilt-runtime artifacts is resolved.

Current status:

- rebuilt `phase01b` runtime direct-read contract: satisfied
- join-repair compatibility with the rebuilt runtime: preserved
- Phase 02 implementation: not started
- Phase 02 planning eligibility: allowed from rebuilt-runtime direct-read evidence

This evidence is sufficient to treat Phase 02 as eligible for a later implementation-planning prompt, while keeping Phase 02 code generation out of scope for this checkpoint.
