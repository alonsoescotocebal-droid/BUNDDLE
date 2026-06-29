from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE02_REBUILT_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE03A_APPROVED_COMPLETION_STATE,
    PHASE03A_REQUIRED_OUTPUTS,
)

from ._runtime_fixture import REPO_ROOT, build_phase03a_runtime, phase03a_audit_rows


class Phase03ASmokeTest(unittest.TestCase):
    REQUIRED_CHECKS = {
        "output_root_external_boundary",
        "repo_no_contamination",
        "manifest_phase03a_state",
        "phase02_runtime_manifest_valid",
        "phase02_validation_clean",
        "phase03a_required_inputs_present",
        "phase02_forbidden_outputs_absent",
        "relation_evidence_tensor_present",
        "relation_evidence_tensor_not_posterior",
        "no_raw_roots_consumed",
        "no_phase01b_runtime_direct_consumption",
        "run_max_lag_edge_lag_preserved",
        "no_global_lag_priority",
        "kinetic_real_only_only",
        "real_plus_interpolated_absent_from_kinetic_likelihood",
        "calibration_route_declared",
        "empirical_or_fallback_route_justified",
        "probability_method_manifest_exists",
        "relation_probability_evidence_tensor_not_posterior",
        "probability_calibration_audit_row_counts_match",
        "semantic_polarity_registry_exists",
        "semantic_compatibility_surface_exists",
        "multilag_profile_preserved",
        "yield_absence_only_if_legitimate",
        "q_values_not_direct_probability",
        "posterior_state_columns_complete",
        "posterior_probabilities_between_zero_and_one",
        "posterior_probabilities_sum_to_one",
        "posterior_not_causal_probability",
        "posterior_not_qa_answer",
        "posterior_not_topology",
        "posterior_not_final_decision",
        "forbidden_outputs_absent",
        "required_artifacts_exist",
        "phase03a_repaired_and_phase03b_plan_allowed",
    }

    def test_manifest_and_required_artifacts_exist(self) -> None:
        runtime_dir, manifest = build_phase03a_runtime()
        self.assertEqual(manifest["phase"], "phase03a")
        self.assertEqual(manifest["phase03a_completion_decision"], PHASE03A_APPROVED_COMPLETION_STATE)
        self.assertEqual(set(manifest["outputs"]), set(PHASE03A_REQUIRED_OUTPUTS))
        for relative_path in manifest["outputs"]:
            self.assertTrue((runtime_dir / Path(relative_path)).exists(), relative_path)

    def test_validation_summary_is_clean(self) -> None:
        rows = phase03a_audit_rows("phase03_validation_summary.tsv")
        check_ids = {row["check_id"] for row in rows}
        self.assertTrue(self.REQUIRED_CHECKS.issubset(check_ids))
        indexed = {row["check_id"]: row for row in rows if row["check_id"] in self.REQUIRED_CHECKS}
        for check_id in self.REQUIRED_CHECKS:
            self.assertEqual(indexed[check_id]["status"], "PASS", check_id)
            self.assertEqual(indexed[check_id]["severity"], "info", check_id)

    def test_cli_smoke_execution(self) -> None:
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase03a",
            "--repo-root",
            str(REPO_ROOT),
            "--phase02-runtime",
            str(DEFAULT_PHASE02_REBUILT_RUNTIME),
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
        self.assertIn("phase03a_complete", completed.stdout)
        self.assertIn(PHASE03A_APPROVED_COMPLETION_STATE, completed.stdout)


if __name__ == "__main__":
    unittest.main()
