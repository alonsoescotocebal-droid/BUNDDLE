from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import PHASE01B_REQUIRED_OUTPUTS, SUPPORTED_PHASES
from sll_probabilistic_pipeline.utils import read_tsv
from sll_probabilistic_pipeline.validation.phase01b import build_phase01b_validation_summary

from ._runtime_fixture import build_phase01b_runtime, phase01b_manifest_payload


class Phase01BDirectReadContractTest(unittest.TestCase):
    REQUIRED_JOIN_OUTPUTS = (
        "data/join_admissibility_contract.tsv",
        "data/many_to_many_origin_diagnostic.tsv",
        "data/policy_surface_non_joinable_registry.tsv",
        "data/lag_invariant_duplicate_origin_audit.tsv",
        "data/phase02_join_contract.tsv",
    )

    OPTIONAL_JOIN_OUTPUTS = (
        "data/per_surface_natural_key_profile.tsv",
        "data/candidate_key_uniqueness_profile.tsv",
    )

    def test_required_outputs_include_join_contract_artifacts(self) -> None:
        self.assertTrue(set(self.REQUIRED_JOIN_OUTPUTS).issubset(PHASE01B_REQUIRED_OUTPUTS))

    def test_supported_phases_now_include_phase02(self) -> None:
        self.assertEqual(
            SUPPORTED_PHASES,
            {"phase01a", "phase01b", "phase01b_join_repair", "phase02", "phase03a", "phase03b1"},
        )
        self.assertIn("phase02", SUPPORTED_PHASES)

    def test_runtime_manifest_lists_optional_join_profiles_when_written(self) -> None:
        manifest = phase01b_manifest_payload()
        outputs = set(manifest["outputs"])
        self.assertTrue(set(self.OPTIONAL_JOIN_OUTPUTS).issubset(outputs))

    def test_validation_fails_if_required_join_contract_artifact_is_missing(self) -> None:
        runtime_dir, manifest = build_phase01b_runtime()
        missing_relative_path = "data/join_admissibility_contract.tsv"
        missing_path = runtime_dir / Path(missing_relative_path)
        join_bundle = {
            "input_join_key_audit.tsv": read_tsv(runtime_dir / "data" / "input_join_key_audit.tsv"),
            "many_to_many_origin_diagnostic.tsv": read_tsv(runtime_dir / "data" / "many_to_many_origin_diagnostic.tsv"),
            "per_surface_natural_key_profile.tsv": read_tsv(runtime_dir / "data" / "per_surface_natural_key_profile.tsv"),
            "candidate_key_uniqueness_profile.tsv": read_tsv(
                runtime_dir / "data" / "candidate_key_uniqueness_profile.tsv"
            ),
            "lag_invariant_duplicate_origin_audit.tsv": read_tsv(
                runtime_dir / "data" / "lag_invariant_duplicate_origin_audit.tsv"
            ),
            "policy_surface_non_joinable_registry.tsv": read_tsv(
                runtime_dir / "data" / "policy_surface_non_joinable_registry.tsv"
            ),
            "join_admissibility_contract.tsv": read_tsv(runtime_dir / "data" / "join_admissibility_contract.tsv"),
            "phase02_join_contract.tsv": read_tsv(runtime_dir / "data" / "phase02_join_contract.tsv"),
        }
        original_bytes = missing_path.read_bytes()
        try:
            missing_path.unlink()
            summary_rows = build_phase01b_validation_summary(
                validation_rows=[],
                runtime_root=runtime_dir,
                required_outputs=PHASE01B_REQUIRED_OUTPUTS,
                discovered_lags=[1, 2, 3, 4],
                output_root_boundary_rows=read_tsv(runtime_dir / "audit" / "output_root_boundary_audit.tsv"),
                repo_contamination_rows=read_tsv(runtime_dir / "audit" / "repo_contamination_audit.tsv"),
                manifest=manifest,
                phase01a_carry_forward_rows=read_tsv(runtime_dir / "data" / "phase01a_policy_carry_forward_audit.tsv"),
                availability_rows=read_tsv(runtime_dir / "data" / "input_surface_availability_audit.tsv"),
                join_bundle=join_bundle,
                stat_outputs={
                    "stat_pcmci_edge_long.tsv": read_tsv(runtime_dir / "data" / "stat_pcmci_edge_long.tsv"),
                    "stat_dense_data_provenance_long.tsv": read_tsv(
                        runtime_dir / "data" / "stat_dense_data_provenance_long.tsv"
                    ),
                },
                kinetic_outputs={
                    "kinetic_growth_primary_long.tsv": read_tsv(
                        runtime_dir / "data" / "kinetic_growth_primary_long.tsv"
                    ),
                    "kinetic_rate_primary_long.tsv": read_tsv(runtime_dir / "data" / "kinetic_rate_primary_long.tsv"),
                    "kinetic_temporal_coupling_primary_long.tsv": read_tsv(
                        runtime_dir / "data" / "kinetic_temporal_coupling_primary_long.tsv"
                    ),
                    "kinetic_yield_primary_long.tsv": read_tsv(runtime_dir / "data" / "kinetic_yield_primary_long.tsv"),
                    "kinetic_disabled_branch_inventory.tsv": read_tsv(
                        runtime_dir / "data" / "kinetic_disabled_branch_inventory.tsv"
                    ),
                },
                empty_audit_rows=read_tsv(runtime_dir / "data" / "input_empty_surface_audit.tsv"),
            )
        finally:
            missing_path.write_bytes(original_bytes)

        required_artifacts_row = next(row for row in summary_rows if row["check_id"] == "required_artifacts_exist")
        self.assertEqual(required_artifacts_row["status"], "FAIL")
        self.assertIn(missing_relative_path, required_artifacts_row["details"])


if __name__ == "__main__":
    unittest.main()
