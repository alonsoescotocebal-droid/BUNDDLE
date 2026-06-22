# SLL — Python pipeline implementation specification v1

## 1. Suggested package layout

```text
sll_probabilistic_pipeline/
  __init__.py
  cli.py
  config.py
  paths.py
  io/
    readers.py
    schema.py
    aliases.py
    provenance.py
  standardize/
    statistical.py
    kinetic.py
    joins.py
  probability/
    calibration.py
    pcmci.py
    conditioned.py
    descriptive.py
    kinetic.py
    posterior.py
    semantic.py
  qa/
    questions.py
    traces.py
    topology.py
    closure.py
  reports/
    technical.py
    human.py
  validation/
    runtime_validator.py
    consistency.py

tests/
  test_path_resolution.py
  test_stat_input_reader.py
  test_kinetic_real_only_rule.py
  test_lag_run_vs_edge_lag.py
  test_probability_not_causality.py
  test_22_questions_contract.py
  test_runtime_validation.py
```

## 2. CLI contract

Minimum CLI:

```bash
python -m sll_probabilistic_pipeline.cli \
  --stat-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs\SLL_REAL_PCMCI_LAG01-04_20260401_174816" \
  --kin-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations\SLL_rates_block_20260426_133037" \
  --out-root "<runtime_output>" \
  --strict
```

Optional discovery mode:

```bash
python -m sll_probabilistic_pipeline.cli \
  --stat-parent "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs" \
  --kin-parent "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations" \
  --out-root "<runtime_output>" \
  --strict
```

Discovery mode must still record exact selected paths and cannot silently pick a candidate.

## 3. Runtime directory contract

```text
runtime_<STAMP>/
  data/
  audit/
  report/
  manifest/
  logs/
```

Raw input files are never modified.

## 4. Required implementation phases

### Phase 0 — inventory only

Produce path and schema audits. No probability calculation.

### Phase 1 — standardized long tables

Produce normalized statistical and kinetic surfaces.

### Phase 2 — probabilistic calibration

Build local-FDR or fallback calibration. Record method.

### Phase 3 — posterior relation states

Compute relation-level posterior support probabilities.

### Phase 4 — 22 calculated questions

Generate QA matrix and evidence traces.

### Phase 5 — reports and closure

Generate technical/human reports only from machine-readable outputs.

## 5. Dependency guidance

Prefer standard scientific Python stack:

```text
pandas
numpy
scipy
scikit-learn
statsmodels
pyarrow optional
pydantic optional
pytest
```

Do not add heavy dependencies without documenting why.

## 6. Deterministic behavior

- Use fixed random seeds when bootstrapping or permutation is implemented.
- Write calibration parameters to JSON.
- Preserve all input row references.
- Ensure outputs are stable enough for tests.
