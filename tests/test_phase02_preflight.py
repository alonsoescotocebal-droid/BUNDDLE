from __future__ import annotations

import unittest

from sll_probabilistic_pipeline.config import DEFAULT_RESULTS_ROOT, PHASE02_BLOCKED_STATE
from sll_probabilistic_pipeline.phase02 import run_phase02
from sll_probabilistic_pipeline.utils import read_tsv, write_tsv

from ._runtime_fixture import REPO_ROOT, clone_phase01b_runtime


class Phase02PreflightTest(unittest.TestCase):
    def test_warning_or_fail_in_phase01b_runtime_blocks_phase02(self) -> None:
        cloned_runtime = clone_phase01b_runtime()
        validation_path = cloned_runtime / "audit" / "phase01b_validation_summary.tsv"
        rows = read_tsv(validation_path)
        rows.append(
            {
                "check_id": "synthetic_warning",
                "status": "WARN",
                "severity": "warning",
                "source_surface": "synthetic",
                "source_row_key": "synthetic",
                "details": "synthetic warning for preflight block test",
            }
        )
        write_tsv(
            validation_path,
            rows,
            ["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
        )

        manifest = run_phase02(
            repo_root=REPO_ROOT,
            phase01b_runtime=cloned_runtime,
            out_root=DEFAULT_RESULTS_ROOT,
            strict=True,
        )
        self.assertEqual(manifest["phase02_completion_decision"], PHASE02_BLOCKED_STATE)
        self.assertEqual(manifest["phase_status"], "phase02_relation_evidence_intake_blocked")


if __name__ == "__main__":
    unittest.main()
