from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE03A_REPAIRED_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE03B1_APPROVED_COMPLETION_STATE,
    PHASE03B1_REQUIRED_OUTPUTS,
)

from ._runtime_fixture import REPO_ROOT, build_phase03b1_runtime, phase03b1_audit_rows


class Phase03B1SmokeTest(unittest.TestCase):
    REQUIRED_CHECKS = {
        "output_root_external_boundary",
        "repo_no_contamination",
        "phase03a_runtime_exists",
        "phase03a_manifest_state_valid",
        "phase03a_validation_clean",
        "phase03a_repaired_decision_valid",
        "phase03a_required_inputs_present",
        "superseded_phase03a_runtime_not_used",
        "relation_probability_tensor_not_posterior",
        "probability_calibration_audit_counts_match",
        "posterior_probabilities_sum_to_one",
        "posterior_not_causal_probability",
        "posterior_not_qa_answer",
        "posterior_not_topology",
        "posterior_not_final_decision",
        "run_max_lag_edge_lag_preserved",
        "kinetic_real_only_only",
        "real_plus_interpolated_absent",
        "raw_roots_not_consumed",
        "phase03a_output_root_boundary_valid",
        "phase03a_repo_contamination_pass",
        "qa22_all_questions_present",
        "qa22_allowed_states_only",
        "qa22_ad_rows_have_direct_trace",
        "qa22_no_narrative_only_closure",
        "intervention_priority_surface_exists",
        "topology_summary_exists",
        "topology_not_causal",
        "q21_q22_final_decision_deferred",
        "required_artifacts_exist",
        "phase03b1_status_complete_waiting_for_phase03b2_plan",
        "question_answer_surface_coverage_exists",
        "question_answer_surface_coverage_complete",
        "question_answer_failure_boundary_exists",
    }

    def test_manifest_and_required_artifacts_exist(self) -> None:
        runtime_dir, manifest = build_phase03b1_runtime()
        self.assertEqual(manifest["phase"], "phase03b1")
        self.assertEqual(manifest["phase03b1_completion_decision"], PHASE03B1_APPROVED_COMPLETION_STATE)
        self.assertEqual(set(manifest["outputs"]), set(PHASE03B1_REQUIRED_OUTPUTS))
        for relative_path in manifest["outputs"]:
            self.assertTrue((runtime_dir / Path(relative_path)).exists(), relative_path)

    def test_validation_summary_is_clean(self) -> None:
        rows = phase03b1_audit_rows("phase03b1_validation_summary.tsv")
        self.assertTrue(rows)
        check_ids = {row["check_id"] for row in rows}
        self.assertTrue(self.REQUIRED_CHECKS.issubset(check_ids))
        for row in rows:
            self.assertEqual(row["status"], "PASS", row["check_id"])
            self.assertEqual(row["severity"], "info", row["check_id"])

    def test_cli_smoke_execution(self) -> None:
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase03b1",
            "--repo-root",
            str(REPO_ROOT),
            "--phase03a-runtime",
            str(DEFAULT_PHASE03A_REPAIRED_RUNTIME),
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
        self.assertIn("phase03b1_complete", completed.stdout)
        self.assertIn(PHASE03B1_APPROVED_COMPLETION_STATE, completed.stdout)


if __name__ == "__main__":
    unittest.main()
