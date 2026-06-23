from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_KIN_ROOT, DEFAULT_RESULTS_ROOT, DEFAULT_STAT_ROOT

from ._runtime_fixture import REPO_ROOT, build_phase01b_runtime, phase01b_manifest_payload, phase01b_rows


class Phase01BSmokeTest(unittest.TestCase):
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
