# AGENTS.md — SLL probabilistic Python pipeline

## Project purpose

Build a Python pipeline that consumes SLL statistical and kinetic outputs and produces probabilistic, machine-readable answers to the 22 canonical questions. The pipeline must replace subjective scoring with calibrated probabilistic evidence synthesis.

## Read first, before editing code

Always read these documents before implementation:

1. `docs/sll_probabilistic_contracts/SLL_CODEX_MACHINE_READABLE_RULES_v1.json`
2. `docs/sll_probabilistic_contracts/SLL_PYTHON_PIPELINE_IMPLEMENTATION_SPEC_v1.md`
3. `docs/sll_probabilistic_contracts/SLL_DATA_CONSUMPTION_AND_INPUT_READER_SPEC_v1.md`
4. `docs/sll_probabilistic_contracts/SLL_PROBABILISTIC_CALCULATION_CONTRACT_v1.md`
5. `docs/sll_probabilistic_contracts/SLL_22_QUESTIONS_RUNTIME_QA_CONTRACT_v1.md`
6. Existing canonical project Markdown files if present in the repo.

## Canonical data roots

Statistical parent:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs
```

Statistical expected run:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816
```

Kinetic parent:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations
```

Kinetic expected run:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037
```

## Non-negotiable data rules

- Statistical layer may use audited interpolated/dense data because PCMCI, partial correlation, interdependence windows, and temporal descriptions require sufficient regular temporal coverage.
- Interpolated statistical data are not new experimental observations; they must retain provenance, audit flags, gates, and links to observed data.
- Kinetic layer must use only real experimental data from `real_only` outputs.
- `real_plus_interpolated` kinetic branch is disabled. Do not use it as kinetic support, likelihood, sensitivity, or complementarity.
- Preserve `run_max_lag` and `edge_lag` as different fields.
- Never choose a single lag as mathematical priority. LAG01-LAG04 are temporal evidence strata.
- Do not interpret p-values, q-values, PCMCI effects, partial correlations, kinetic rates, or final scores as causal probabilities.
- Probabilities are posterior support/compatibility probabilities for internal relational states, not final proof of mechanism.

## Implementation behavior

- Work in checkpoints.
- Do not overwrite raw input folders.
- Create deterministic scripts rather than notebook-only logic.
- Every generated output must include provenance fields where applicable: `source_path`, `source_surface`, `source_row_key`, `source_row_number`, `direct_read_yes_no`, `inference_used_yes_no`, `trace_id`.
- Before merging layers, profile keys, null rates, duplicated keys, and join coverage.
- If a required input surface is missing or empty, write an audit row; do not silently drop it.
- If any mandatory QA question becomes `internal_failure_localized`, final decision must be `NO-GO`.

## Required validation before declaring completion

At minimum, run:

```bash
python -m py_compile <all_project_python_files>
python -m pytest -q
python -m sll_probabilistic_pipeline.cli --stat-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816" --kin-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037" --out-root <runtime_output>
python -m sll_probabilistic_pipeline.validate_runtime --runtime <runtime_output>
```

If the package name or CLI changes, update this file and the tests in the same commit.

## Done means

A phase is done only when the expected TSV/JSON/Markdown artifacts are generated, tests pass, and the runtime validation report reads the artifacts directly. Narrative explanations are not closure authority.
