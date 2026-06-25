# PHASE02_BLOCKED_RUNTIME_DIRECT_READ_REQUIRED

## Controlling instruction

This note is controlled by:

```text
C:\Users\X412\Downloads\CODEX_PROMPT_PHASE02_PLAN_FROM_JOIN_REPAIR_ALLOWED_STATE.md
```

The prompt's direct-read requirements are applied literally for this checkpoint.

## Repository verification

- Repository root:
  `D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE`
- Verified SHA:
  `89e258de5cb35f1c3ac086ccf5f14179b0ffb46f`
- Git worktree status at verification time:
  `clean`

## Validation commands

Previously verified during this readiness check:

```text
python -m py_compile <all project python files>  -> PASS (41 Python files)
python -m pytest -q                              -> PASS (38 tests)
```

## Direct-read matrix

Expected runtime root:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS
```

### Rebuilt Phase 01B runtime

Runtime:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260624_145643
```

Required files and direct-read status:

| Relative path | Status |
| --- | --- |
| `manifest/runtime_manifest.json` | `present` |
| `audit/phase01b_validation_summary.tsv` | `present` |
| `data/input_join_key_audit.tsv` | `present` |
| `data/join_admissibility_contract.tsv` | `missing` |
| `data/many_to_many_origin_diagnostic.tsv` | `missing` |
| `data/policy_surface_non_joinable_registry.tsv` | `missing` |
| `data/lag_invariant_duplicate_origin_audit.tsv` | `missing` |
| `data/phase02_join_contract.tsv` | `missing` |

Observed direct-read summary:

- `manifest/runtime_manifest.json` is present.
- `audit/phase01b_validation_summary.tsv` is present and contains `0 WARN` rows and `0 FAIL/error` rows.
- `data/input_join_key_audit.tsv` is present.
- No Phase 02 output artifacts are present in this runtime.
- The prompt-required direct-read artifact set is incomplete.

### Join-repair runtime

Runtime:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_JOIN_ROOT_CAUSE_REPAIR_20260624_145522
```

Required files and direct-read status:

| Relative path | Status |
| --- | --- |
| `manifest/runtime_manifest.json` | `present` |
| `audit/many_to_many_root_cause_validation_summary.tsv` | `present` |
| `data/input_join_key_audit_original.tsv` | `present` |
| `data/input_join_key_audit.tsv` | `present` |
| `data/join_admissibility_contract.tsv` | `present` |
| `data/phase02_join_contract.tsv` | `present` |
| `data/many_to_many_origin_diagnostic.tsv` | `present` |
| `data/policy_surface_non_joinable_registry.tsv` | `present` |
| `data/lag_invariant_duplicate_origin_audit.tsv` | `present` |

Observed direct-read summary:

- `manifest/runtime_manifest.json` is present and contains `phase02_plan_decision = PHASE02_PLAN_ALLOWED`.
- `audit/many_to_many_root_cause_validation_summary.tsv` is present and contains `0 WARN` rows and `0 FAIL/error` rows.
- No Phase 02 output artifacts are present in this runtime.
- The repair runtime is direct-read complete for the prompt-required file set.

## Blocker decision

Case B applies.

Phase 02 implementation is blocked because the rebuilt `phase01b` runtime does not directly expose the full mandatory direct-read contract required by the controlling prompt, even though the join-repair runtime is clean and complete. The missing rebuilt-runtime files are:

- `data/join_admissibility_contract.tsv`
- `data/many_to_many_origin_diagnostic.tsv`
- `data/policy_surface_non_joinable_registry.tsv`
- `data/lag_invariant_duplicate_origin_audit.tsv`
- `data/phase02_join_contract.tsv`

Repair-only artifacts are not accepted as substitutes for missing rebuilt-runtime reads under this prompt.

## Non-scope

- Do not implement `phase02` in this checkpoint.
- Do not add Phase 02 runtime or code artifacts in this checkpoint.
- Do not change `sll_probabilistic_pipeline/cli.py`, `sll_probabilistic_pipeline/config.py`, `sll_probabilistic_pipeline/paths.py`, or tests in this checkpoint.
- Do not add `phase02` to `SUPPORTED_PHASES`.
- Do not introduce `phase02.py`.
- Do not extend manifests or validators in this checkpoint.

Future Phase 02 work, if later authorized, must consume only normalized `phase01b` and join-repair outputs plus `phase02_join_contract.tsv`. It must not read raw statistical roots or raw kinetic roots directly, and it must not calculate posterior probabilities in Phase 02.

## Unblock condition

Phase 02 authorization may be reconsidered only after the expected rebuilt `phase01b` runtime directly exposes the full prompt-required file set and still satisfies all of the following:

- clean validation with `0 WARN` rows and `0 FAIL/error` rows
- no Phase 02 outputs present in the rebuilt `phase01b` runtime
- no Phase 02 outputs present in the join-repair runtime
- the direct-read evidence continues to support the existing resolved join-consumption semantics without reopening the many-to-many warning as tolerable risk
