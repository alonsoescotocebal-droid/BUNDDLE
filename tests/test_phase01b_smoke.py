from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_KIN_ROOT, DEFAULT_RESULTS_ROOT, DEFAULT_STAT_ROOT

from ._runtime_fixture import REPO_ROOT, build_phase01b_runtime, phase01b_audit_rows, phase01b_rows


class Phase01BSmokeTest(unittest.TestCase):
    REQUIRED_VALIDATION_CHECKS = {
        "output_root_external_boundary",
        "repo_no_contamination",
        "manifest_phase01b_state",
        "no_phase02_outputs_present",
        "phase01a_policy_carry_forward_immutable",
        "statistical_lag01_lag04_coverage",
        "run_max_lag_edge_lag_separation",
        "edge_lag_le_run_max_lag",
        "stat_dense_provenance_present",
        "stat_dense_interpolation_flags_preserved",
        "stat_dense_direct_read_trace_present",
        "kinetic_primary_real_only_only",
        "kinetic_real_plus_interpolated_disabled_inventory",
        "kinetic_yield_empty_legitimate",
        "input_surface_availability_no_missing_required",
        "join_audit_exists",
        "join_many_to_many_risk_profiled_not_joined",
        "required_artifacts_exist",
    }

    def test_manifest_and_required_artifacts_exist(self) -> None:
        runtime_dir, manifest = build_phase01b_runtime()
        self.assertEqual(manifest["phase"], "phase01b")
        self.assertEqual(manifest["phase_status"], "phase01b_complete_waiting_for_phase02_approval")
        self.assertEqual(manifest["pipeline_global_status"], "not_closed")
        self.assertEqual(manifest["final_go_no_go"], "not_applicable_for_phase01b")
        for relative_path in manifest["outputs"]:
            self.assertTrue((runtime_dir / Path(relative_path)).exists(), relative_path)

    def test_repo_contamination_audit_passes(self) -> None:
        runtime_dir, _ = build_phase01b_runtime()
        rows = phase01b_rows("phase01a_policy_carry_forward_audit.tsv")
        self.assertTrue(rows)
        contamination_rows = [
            row
            for row in (runtime_dir / "audit" / "repo_contamination_audit.tsv").read_text(encoding="utf-8").splitlines()
            if "pass_no_new_repo_runtime_outputs" in row
        ]
        self.assertTrue(contamination_rows)

    def test_validation_summary_contains_required_invariants(self) -> None:
        rows = phase01b_audit_rows("phase01b_validation_summary.tsv")
        check_ids = {row["check_id"] for row in rows}
        self.assertTrue(self.REQUIRED_VALIDATION_CHECKS.issubset(check_ids))

        indexed = {row["check_id"]: row for row in rows if row["check_id"] in self.REQUIRED_VALIDATION_CHECKS}
        for check_id in self.REQUIRED_VALIDATION_CHECKS - {"join_many_to_many_risk_profiled_not_joined"}:
            self.assertEqual(indexed[check_id]["status"], "PASS", check_id)
        join_risk = indexed["join_many_to_many_risk_profiled_not_joined"]
        self.assertIn(join_risk["status"], {"PASS", "WARN"})
        if join_risk["status"] == "WARN":
            self.assertEqual(join_risk["severity"], "warning")

    def test_cli_smoke_execution(self) -> None:
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase01b",
            "--repo-root",
            str(REPO_ROOT),
            "--stat-root",
            str(DEFAULT_STAT_ROOT),
            "--kin-root",
            str(DEFAULT_KIN_ROOT),
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
        self.assertIn("phase01b_complete", completed.stdout)


if __name__ == "__main__":
    unittest.main()
