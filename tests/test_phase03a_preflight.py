from __future__ import annotations

import unittest

from sll_probabilistic_pipeline.config import DEFAULT_RESULTS_ROOT, PHASE03A_BLOCKED_STATE
from sll_probabilistic_pipeline.phase03a import run_phase03a
from sll_probabilistic_pipeline.utils import read_tsv, write_tsv

from ._runtime_fixture import REPO_ROOT, clone_phase02_runtime


class Phase03APreflightTest(unittest.TestCase):
    def test_warning_or_fail_in_phase02_runtime_blocks_phase03a(self) -> None:
        cloned_runtime = clone_phase02_runtime()
        validation_path = cloned_runtime / "audit" / "phase02_validation_summary.tsv"
        rows = read_tsv(validation_path)
        rows.append(
            {
                "check_id": "synthetic_warning",
                "status": "WARN",
                "severity": "warning",
                "source_surface": "synthetic",
                "source_row_key": "synthetic",
                "details": "synthetic warning for phase03a preflight block test",
            }
        )
        write_tsv(
            validation_path,
            rows,
            ["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
        )

        manifest = run_phase03a(
            repo_root=REPO_ROOT,
            phase02_runtime=cloned_runtime,
            out_root=DEFAULT_RESULTS_ROOT,
            strict=True,
        )
        self.assertEqual(manifest["phase03a_completion_decision"], PHASE03A_BLOCKED_STATE)
        self.assertEqual(manifest["phase_status"], "phase03a_probabilistic_calibration_blocked")

    def test_forbidden_phase02_output_blocks_phase03a(self) -> None:
        cloned_runtime = clone_phase02_runtime()
        forbidden_path = cloned_runtime / "data" / "posterior_relation_state.tsv"
        forbidden_path.write_text("forbidden\n", encoding="utf-8")

        manifest = run_phase03a(
            repo_root=REPO_ROOT,
            phase02_runtime=cloned_runtime,
            out_root=DEFAULT_RESULTS_ROOT,
            strict=True,
        )
        self.assertEqual(manifest["phase03a_completion_decision"], PHASE03A_BLOCKED_STATE)


if __name__ == "__main__":
    unittest.main()
