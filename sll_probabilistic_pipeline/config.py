"""Configuration constants for the SLL probabilistic pipeline."""

from __future__ import annotations

from pathlib import Path

DEFAULT_STAT_ROOT = Path(
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\runs"
    r"\SLL_REAL_PCMCI_LAG01-04_20260401_174816"
)
DEFAULT_KIN_ROOT = Path(
    r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\INTERDEPENDENCIA_ANA_ARTIGOS\Rates calculations"
    r"\SLL_rates_block_20260426_133037"
)

SUPPORTED_PHASES = {"phase01a"}

PHASE01A_OUTPUTS = (
    "growth_variable_identity_audit.tsv",
    "acetate_dual_role_audit.tsv",
    "canonical_component_alias_registry.tsv",
    "component_role_by_condition_audit.tsv",
    "cross_layer_join_identity_policy.tsv",
)

SCENARIO_ALIASES = {
    "MIX_MAX": "MIX_MAX",
    "Mix-max": "MIX_MAX",
    "MAX": "MAX",
    "Max concentration": "MAX",
    "MIN": "MIN",
    "Min concentration": "MIN",
}

MANUAL_POLICY_SURFACE = "SLL_CANONICAL_IDENTITY_POLICY_OD_ACETATE_v1.md"

