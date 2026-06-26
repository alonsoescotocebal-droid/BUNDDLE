# PHASE02_IMPLEMENTATION_PLAN_REWRITTEN_FULL_DETAIL_v2

## 0. Control de version y proposito

**Documento controlador:** `docs/PHASE02_IMPLEMENTATION_PLAN_REWRITTEN_FULL_DETAIL_v2.md`  
**Fase:** Phase 02 - Relation Evidence Intake Only  
**Estado esperado al terminar implementacion:** `PHASE02_RELATION_EVIDENCE_INTAKE_COMPLETE_WAITING_FOR_PHASE03_PLAN`  
**SHA controlador de arranque:** `b3a3299164318ef71885ed6d1f801b4aef96b53e`  
**Repositorio autorizado para edicion:**  
`D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE`

Este documento existe para impedir que Phase 02 se convierta prematuramente en posterior probabilistico, QA22, topologia, reporte final o cierre global. Phase 02 solo debe construir una capa de ingesta de evidencia relacional a partir de los outputs normalizados de Phase 01B y de los contratos de join ya resueltos.

---

## 1. Decision de alcance

### 1.1 Lo que Phase 02 si debe hacer

Phase 02 debe consumir exclusivamente el runtime rebuilt Phase 01B validado:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628
```

y construir superficies normalizadas para preparar evidencia relacional por:

- eje temporal PCMCI;
- eje descriptivo por variable/ventana;
- eje interdependencia descriptiva por ventana;
- eje condicionado/partial-correlation global;
- eje cinetico real_only;
- eje de contrato de join Phase 02;
- eje de auditoria semantica y elegibilidad relacional;
- tensor de evidencia relacional sin posterior.

### 1.2 Lo que Phase 02 no debe hacer

Phase 02 no debe implementar ni producir:

```text
posterior probabilities
posterior_relation_state.tsv/json
QA22
runtime_question_answer_matrix.tsv/json
question_answer_evidence_trace.tsv
network_topology_summary.tsv/json
final_static_release_decision.json
final_machine_readable_consistency_audit.tsv
TECHNICAL_QUESTION_ANSWER_REPORT_<STAMP>.md
HUMAN_REPORT_<STAMP>.md
global GO/NO-GO closure
Phase 03
```

### 1.3 Regla de lectura externa

Phase 02 no debe leer las raices crudas:

```text
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs
D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations
```

salvo que una validacion explicita de existencia externa sea anadida como check no consumidor. La construccion relacional debe partir de los TSV/JSON normalizados ya generados por Phase 01B.

---

## 2. Entradas obligatorias de Phase 02

Phase 02 debe recibir un argumento explicito:

```text
--phase01b-runtime "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628"
```

y debe validar que el runtime contiene al menos:

```text
manifest/runtime_manifest.json
audit/phase01b_validation_summary.tsv
data/input_path_resolution_audit.tsv
data/input_surface_availability_audit.tsv
data/input_schema_inventory.tsv
data/input_data_basis_policy_audit.tsv
data/growth_variable_identity_audit.tsv
data/acetate_dual_role_audit.tsv
data/canonical_component_alias_registry.tsv
data/component_role_by_condition_audit.tsv
data/cross_layer_join_identity_policy.tsv
data/phase01a_policy_carry_forward_audit.tsv
data/stat_pcmci_edge_long.tsv
data/stat_pcmci_model_context_long.tsv
data/stat_descriptive_node_state_long.tsv
data/stat_interdependence_pair_window_long.tsv
data/stat_conditioned_pair_global_long.tsv
data/stat_dense_data_provenance_long.tsv
data/kinetic_growth_primary_long.tsv
data/kinetic_rate_primary_long.tsv
data/kinetic_temporal_coupling_primary_long.tsv
data/kinetic_yield_primary_long.tsv
data/kinetic_disabled_branch_inventory.tsv
data/kinetic_traceability_long.tsv
data/input_join_key_audit.tsv
data/many_to_many_origin_diagnostic.tsv
data/per_surface_natural_key_profile.tsv
data/candidate_key_uniqueness_profile.tsv
data/lag_invariant_duplicate_origin_audit.tsv
data/policy_surface_non_joinable_registry.tsv
data/join_admissibility_contract.tsv
data/phase02_join_contract.tsv
data/input_empty_surface_audit.tsv
```

---

## 3. Preflight obligatorio

Antes de crear cualquier output Phase 02, el preflight debe validar:

| Check ID | Regla |
|---|---|
| `phase01b_runtime_exists` | `--phase01b-runtime` existe fisicamente. |
| `phase01b_manifest_state_valid` | Manifest declara `phase=phase01b`, `phase_status=phase01b_complete_waiting_for_phase02_approval`, `pipeline_global_status=not_closed`. |
| `phase01b_validation_clean` | `audit/phase01b_validation_summary.tsv` tiene 0 `WARN`/`warning` y 0 `FAIL`/`error`. |
| `phase01b_required_inputs_present` | Todas las entradas obligatorias existen. |
| `phase02_join_contract_present` | `data/phase02_join_contract.tsv` existe, tiene filas y todas estan `resolution_state=resolved`. |
| `join_admissibility_contract_present` | `data/join_admissibility_contract.tsv` existe, tiene filas y todas estan resueltas. |
| `many_to_many_not_reopened` | Ningun join relacional amplio se ejecuta contra filas de medicion fuera del contrato; `projection_only` y `policy_lookup_only` se respetan. |
| `kinetic_real_only_only` | Cualquier superficie cinetica usada tiene `branch=real_only`; `real_plus_interpolated` solo puede aparecer como deshabilitada. |
| `no_raw_roots_consumed` | Phase 02 no lee directamente roots crudos estadisticos/cineticos. |
| `no_forbidden_outputs_before_run` | El runtime Phase 02 no contiene outputs de posterior, QA22, topologia o cierre final. |

Si falla cualquier preflight, Phase 02 debe detenerse y escribir:

```text
docs/PHASE02_RELATION_EVIDENCE_INTAKE_BLOCKED.md
```

o un runtime de bloqueo externo, si ya se inicio ejecucion, con decision:

```text
PHASE02_RELATION_EVIDENCE_INTAKE_BLOCKED
```

---

## 4. Cambios de codigo autorizados

### 4.1 `config.py`

Anadir:

```python
SUPPORTED_PHASES = {"phase01a", "phase01b", "phase01b_join_repair", "phase02"}
PHASE02_RUNTIME_PREFIX = "SLL_PHASE02_RELATION_EVIDENCE_INTAKE_"
```

Definir `PHASE02_REQUIRED_INPUTS` y `PHASE02_REQUIRED_OUTPUTS`.

### 4.2 `cli.py`

Anadir dispatch para:

```text
--phase phase02
--phase01b-runtime <PATH>
--repo-root <PATH>
--out-root <PATH>
--strict
```

No exigir `--stat-root` ni `--kin-root` para Phase 02.

### 4.3 `paths.py`

Anadir resolver:

```python
resolve_phase02_paths(repo_root, phase01b_runtime, out_root, strict)
```

Reglas:

- repo_root debe estar dentro del repositorio autorizado;
- out_root debe estar bajo `PREDICTOR RESULTADOS`;
- phase01b_runtime debe estar bajo `PREDICTOR RESULTADOS`;
- Phase 02 no recibe raw roots;
- runtime output debe crearse con prefijo `SLL_PHASE02_RELATION_EVIDENCE_INTAKE_`.

### 4.4 `phase02.py`

Crear orquestador de runtime Phase 02.

Debe:

1. resolver paths;
2. crear runtime externo;
3. leer solo outputs de Phase 01B;
4. ejecutar preflight;
5. construir superficies de evidencia;
6. escribir artefactos;
7. escribir manifest;
8. ejecutar validacion;
9. no generar outputs prohibidos.

### 4.5 `standardize` o nuevo paquete `evidence`

Crear modulo para construir las superficies:

```text
relation_anchor_registry.tsv
stat_temporal_pcmci_evidence_intake.tsv
stat_descriptive_evidence_intake.tsv
stat_interdependence_evidence_intake.tsv
stat_conditioned_pair_evidence_intake.tsv
kinetic_growth_evidence_intake.tsv
kinetic_rate_evidence_intake.tsv
kinetic_temporal_coupling_evidence_intake.tsv
kinetic_yield_evidence_intake.tsv
phase02_join_contract_consumption_audit.tsv
relation_evidence_tensor.tsv
```

### 4.6 `validation/phase02.py`

Crear validador especifico Phase 02.

---

## 5. Outputs obligatorios de Phase 02

Runtime externo:

```text
SLL_PHASE02_RELATION_EVIDENCE_INTAKE_<STAMP>/
  data/
  audit/
  manifest/
  logs/
```

### 5.1 Manifest

```text
manifest/runtime_manifest.json
```

Campos minimos:

```text
phase=phase02
phase_status=phase02_relation_evidence_intake_complete_waiting_for_phase03_plan
pipeline_global_status=not_closed
final_go_no_go=not_applicable_for_phase02
phase01b_runtime=<path>
out_root=<path>
runtime_root=<path>
outputs=<PHASE02_REQUIRED_OUTPUTS>
forbidden_outputs_absent=yes
```

### 5.2 Data outputs

```text
data/phase02_input_runtime_manifest_audit.tsv
data/phase02_input_surface_manifest.tsv
data/phase02_preflight_audit.tsv
data/relation_anchor_registry.tsv
data/stat_temporal_pcmci_evidence_intake.tsv
data/stat_descriptive_evidence_intake.tsv
data/stat_interdependence_evidence_intake.tsv
data/stat_conditioned_pair_evidence_intake.tsv
data/kinetic_growth_evidence_intake.tsv
data/kinetic_rate_evidence_intake.tsv
data/kinetic_temporal_coupling_evidence_intake.tsv
data/kinetic_yield_evidence_intake.tsv
data/phase02_join_contract_consumption_audit.tsv
data/relation_evidence_tensor.tsv
data/phase02_forbidden_output_scan.tsv
data/phase02_empty_or_absent_evidence_audit.tsv
```

### 5.3 Audit outputs

```text
audit/output_root_boundary_audit.tsv
audit/repo_contamination_audit.tsv
audit/phase02_validation_summary.tsv
```

### 5.4 Documentation output

```text
docs/PHASE02_RELATION_EVIDENCE_INTAKE_IMPLEMENTATION_AUDIT.md
```

---

## 6. Esquemas minimos de outputs

### 6.1 `relation_anchor_registry.tsv`

Campos obligatorios:

```text
relation_anchor_id
anchor_scope
target_component_id
perturbator_component_id
scenario_canonical
condition_role
condition_id
replicate
window_label
run_max_lag
edge_lag
source_surfaces
anchor_origin
join_contract_role
direct_read_yes_no
inference_used_yes_no
trace_id
```

### 6.2 `stat_temporal_pcmci_evidence_intake.tsv`

```text
relation_anchor_id
source_surface
source_row_key
run_max_lag
edge_lag
source_component_id
target_component_id
effect_sign
effect_value
p_value
q_value
temporal_evidence_stat
not_probability_yes_no
direct_read_yes_no
trace_id
```

### 6.3 `stat_descriptive_evidence_intake.tsv`

```text
relation_anchor_id
source_surface
source_row_key
canonical_component_id
scenario_canonical
condition_role
condition_id
replicate
window_label
descriptive_measure_type
descriptive_value
descriptive_direction
projection_role
join_admissibility
direct_read_yes_no
trace_id
```

### 6.4 `stat_interdependence_evidence_intake.tsv`

```text
relation_anchor_id
source_surface
source_row_key
left_component_id
right_component_id
scenario_canonical
condition_role
condition_id
replicate
window_label
interdependence_measure
interdependence_value
pair_role
direct_read_yes_no
trace_id
```

### 6.5 `stat_conditioned_pair_evidence_intake.tsv`

```text
relation_anchor_id
source_surface
source_row_key
left_component_id
right_component_id
conditioned_measure
conditioned_value
conditioned_sign
direction_allowed_yes_no
direct_read_yes_no
trace_id
```

### 6.6 `kinetic_*_evidence_intake.tsv`

Todos los outputs cineticos deben incluir:

```text
relation_anchor_id
source_surface
source_row_key
branch
canonical_component_id
scenario_canonical
condition_role
condition_id
replicate
time_window_or_interval
kinetic_measure_type
kinetic_value
kinetic_direction
kinetic_role
kinetic_support_status
direct_read_yes_no
trace_id
```

y deben cumplir:

```text
branch=real_only
```

si contienen filas de soporte cinetico real.

### 6.7 `relation_evidence_tensor.tsv`

Debe ser tensor de evidencia, no posterior.

Campos obligatorios:

```text
relation_anchor_id
target_component_id
perturbator_component_id
scenario_canonical
condition_role
condition_id
replicate
window_label
run_max_lag
edge_lag
has_temporal_pcmci_evidence
has_descriptive_evidence
has_interdependence_evidence
has_conditioned_pair_evidence
has_kinetic_growth_evidence
has_kinetic_rate_evidence
has_kinetic_temporal_coupling_evidence
has_kinetic_yield_evidence
evidence_layer_count
evidence_conflict_flag
join_contract_role
relation_intake_status
not_posterior_yes_no
direct_read_yes_no
inference_used_yes_no
trace_id
```

Prohibido incluir:

```text
posterior_probability
P_signal
P_state
causal_probability
final_score
qa_answer_state
network_degree
final_go_no_go
```

---

## 7. Reglas de join Phase 02

Phase 02 debe consumir `phase02_join_contract.tsv` y respetar:

```text
projection_only
policy_lookup_only
joinable
forbidden
```

Reglas:

- descriptivo -> tasa cinetica: `projection_only`;
- descriptivo -> acoplamiento cinetico: `projection_only`;
- growth identity policy -> kinetic growth: `policy_lookup_only`;
- ninguna tabla de politica puede tratarse como medicion;
- ningun many-to-many broad join puede usarse como join de mediciones;
- las relaciones pueden compartir `relation_anchor_id` por proyeccion, pero debe quedar auditado.

---

## 8. Reglas de lag

Obligatorio:

```text
run_max_lag != edge_lag como conceptos separados
```

Prohibido:

```text
lag_priority_global
default_to_LAG03
default_to_LAG02
select_single_lag_for_all_relations
```

Permitido en Phase 02:

- conservar todos los lags;
- registrar evidencia por `run_max_lag` y `edge_lag`;
- marcar ausencia de lag para capas no temporales.

---

## 9. Reglas de cinetica

- Cinetica usa exclusivamente `real_only`.
- `real_plus_interpolated` permanece deshabilitada.
- Si `kinetic_yield_primary_long.tsv` esta vacio, debe generar ausencia legitima auditada, no falla automatica.
- No se permite que cinetica upstream desaparezca sin `phase02_empty_or_absent_evidence_audit.tsv`.

---

## 10. Validacion Phase 02

`audit/phase02_validation_summary.tsv` debe contener como minimo:

```text
output_root_external_boundary
repo_no_contamination
manifest_phase02_state
phase01b_runtime_manifest_valid
phase01b_validation_clean
phase02_required_inputs_present
phase02_join_contract_consumed
no_raw_roots_consumed
kinetic_real_only_only
real_plus_interpolated_disabled
run_max_lag_edge_lag_preserved
no_global_lag_priority
relation_anchor_registry_exists
relation_evidence_tensor_exists
relation_evidence_tensor_not_posterior
forbidden_outputs_absent
required_artifacts_exist
phase02_status_complete_waiting_for_phase03_plan
```

Cada fila debe tener:

```text
check_id
status
severity
source_surface
source_row_key
details
```

El runtime solo puede considerarse valido si:

```text
0 WARN/warning
0 FAIL/error
```

---

## 11. Tests minimos

Agregar tests:

```text
tests/test_phase02_path_resolution.py
tests/test_phase02_preflight.py
tests/test_phase02_no_raw_roots.py
tests/test_phase02_join_contract_consumption.py
tests/test_phase02_kinetic_real_only.py
tests/test_phase02_lag_preservation.py
tests/test_phase02_forbidden_outputs.py
tests/test_phase02_smoke.py
```

Los tests deben verificar:

- Phase 02 se agrega a `SUPPORTED_PHASES`;
- CLI acepta `--phase phase02`;
- Phase 02 no requiere `--stat-root` ni `--kin-root`;
- Phase 02 requiere `--phase01b-runtime`;
- runtime Phase 01B invalido bloquea ejecucion;
- warnings/failures en Phase 01B bloquean ejecucion;
- `phase02_join_contract.tsv` se consume;
- `real_plus_interpolated` no aparece como soporte;
- `relation_evidence_tensor.tsv` no contiene columnas prohibidas;
- no se generan outputs de posterior, QA22, topologia, reportes o cierre final.

---

## 12. Comandos de validacion esperados

```text
python -m py_compile <all project python files>
python -m pytest -q
python -m sll_probabilistic_pipeline.cli --phase phase02 --repo-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR\BUNDDLE" --phase01b-runtime "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS\SLL_PHASE01B_NORMALIZED_INPUT_READER_20260625_094628" --out-root "D:\INTERDEPDNDENCIA_ARTIGOS_ANA\PREDICTOR PROBABILIDAD\PREDICTOR RESULTADOS" --strict
```

---

## 13. Documento de cierre de implementacion Phase 02

Al terminar implementacion, escribir:

```text
docs/PHASE02_RELATION_EVIDENCE_INTAKE_IMPLEMENTATION_AUDIT.md
```

Debe registrar:

- SHA inicial;
- SHA final;
- git status antes/despues;
- comandos ejecutados;
- resultados de py_compile;
- resultados de pytest;
- ruta de runtime;
- conteos de artefactos;
- `phase02_validation_summary.tsv` con 0 warnings/fails;
- ausencia de outputs prohibidos;
- decision:

```text
PHASE02_RELATION_EVIDENCE_INTAKE_COMPLETE_WAITING_FOR_PHASE03_PLAN
```

---

## 14. Condiciones de bloqueo

Crear bloqueo si:

```text
phase01b runtime no existe
phase01b validation tiene WARN o FAIL
phase02_join_contract falta o no esta resuelto
se requiere leer raw roots para construir evidencia
real_plus_interpolated aparece como soporte
relation_evidence_tensor necesita posterior para existir
se detectan outputs prohibidos
sandbox/helper impide escribir de forma segura dentro del repo
```

Bloqueo esperado:

```text
PHASE02_RELATION_EVIDENCE_INTAKE_BLOCKED
```

---

## 15. Fase siguiente permitida despues de Phase 02

Si Phase 02 termina correctamente, la siguiente fase no es implementacion automatica de posterior. La siguiente fase debe ser:

```text
PHASE03_PROBABILISTIC_CALIBRATION_PLAN
```

Phase 03 debera planificar calibracion probabilistica, posterior, QA22 y salidas interpretativas, pero solo despues de leer directamente el runtime Phase 02 valido.
