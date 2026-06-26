from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE01B_REBUILT_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE02_APPROVED_COMPLETION_STATE,
    PHASE02_REQUIRED_OUTPUTS,
)

from ._runtime_fixture import REPO_ROOT, build_phase02_runtime, phase02_audit_rows


class Phase02SmokeTest(unittest.TestCase):
    REQUIRED_CHECKS = {
        "output_root_external_boundary",
        "repo_no_contamination",
        "manifest_phase02_state",
        "phase01b_runtime_manifest_valid",
        "phase01b_validation_clean",
        "phase02_required_inputs_present",
        "phase02_join_contract_consumed",
        "join_admissibility_contract_consumed",
        "no_raw_roots_consumed",
        "kinetic_real_only_only",
        "real_plus_interpolated_disabled",
        "run_max_lag_edge_lag_preserved",
        "no_global_lag_priority",
        "relation_anchor_registry_exists",
        "relation_evidence_tensor_exists",
        "relation_evidence_tensor_not_posterior",
        "forbidden_outputs_absent",
        "required_artifacts_exist",
        "phase02_status_complete_waiting_for_phase03_plan",
    }

    def test_manifest_and_required_artifacts_exist(self) -> None:
        runtime_dir, manifest = build_phase02_runtime()
        self.assertEqual(manifest["phase"], "phase02")
        self.assertEqual(manifest["phase02_completion_decision"], PHASE02_APPROVED_COMPLETION_STATE)
        self.assertEqual(set(manifest["outputs"]), set(PHASE02_REQUIRED_OUTPUTS))
        for relative_path in manifest["outputs"]:
            self.assertTrue((runtime_dir / Path(relative_path)).exists(), relative_path)

    def test_validation_summary_is_clean(self) -> None:
        rows = phase02_audit_rows("phase02_validation_summary.tsv")
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
            "phase02",
            "--repo-root",
            str(REPO_ROOT),
            "--phase01b-runtime",
            str(DEFAULT_PHASE01B_REBUILT_RUNTIME),
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
        self.assertIn("phase02_complete", completed.stdout)
        self.assertIn(PHASE02_APPROVED_COMPLETION_STATE, completed.stdout)


if __name__ == "__main__":
    unittest.main()
