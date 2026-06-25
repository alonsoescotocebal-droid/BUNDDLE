from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_RESULTS_ROOT

from ._runtime_fixture import (
    REPO_ROOT,
    build_phase01b_runtime,
    build_phase01b_join_repair_runtime,
    phase01b_join_repair_audit_rows,
)


class Phase01BJoinRepairSmokeTest(unittest.TestCase):
    REQUIRED_CHECKS = {
        "output_root_external_boundary",
        "repo_no_contamination",
        "input_phase01b_runtime_manifest_state",
        "input_phase01b_validation_preflight",
        "many_to_many_root_cause_resolved",
        "no_unresolved_many_to_many_warn",
        "stat_descriptive_broad_key_root_cause_identified",
        "stat_descriptive_lag_invariant_duplicates_explained",
        "stat_descriptive_time_window_multiplicity_explained",
        "kinetic_condition_replicate_granularity_explained",
        "growth_identity_policy_surface_not_joined_as_measurement",
        "policy_surface_non_joinable_registry_exists",
        "join_admissibility_contract_complete",
        "phase02_join_contract_ready",
        "no_phase02_artifacts_generated",
        "required_artifacts_exist",
    }

    def test_manifest_and_validation_are_clean(self) -> None:
        runtime_dir, manifest = build_phase01b_join_repair_runtime()
        self.assertEqual(manifest["phase"], "phase01b_join_repair")
        self.assertEqual(manifest["phase02_plan_decision"], "PHASE02_PLAN_ALLOWED")
        for relative_path in manifest["outputs"]:
            self.assertTrue((runtime_dir / Path(relative_path)).exists(), relative_path)

        rows = phase01b_join_repair_audit_rows("many_to_many_root_cause_validation_summary.tsv")
        indexed = {row["check_id"]: row for row in rows if row["check_id"] in self.REQUIRED_CHECKS}
        self.assertTrue(self.REQUIRED_CHECKS.issubset(indexed.keys()))
        for row in indexed.values():
            self.assertEqual(row["status"], "PASS", row["check_id"])
            self.assertEqual(row["severity"], "info", row["check_id"])

    def test_cli_smoke_execution(self) -> None:
        phase01b_runtime, _ = build_phase01b_runtime()
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase01b_join_repair",
            "--repo-root",
            str(REPO_ROOT),
            "--phase01b-runtime",
            str(phase01b_runtime),
            "--out-root",
            str(DEFAULT_RESULTS_ROOT),
            "--strict",
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("phase01b_join_repair_complete", completed.stdout)
        self.assertIn("PHASE02_PLAN_ALLOWED", completed.stdout)


if __name__ == "__main__":
    unittest.main()
