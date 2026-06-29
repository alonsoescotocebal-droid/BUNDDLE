from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE03A_SUPERSEDED_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE03B1_BLOCKED_STATE,
)
from sll_probabilistic_pipeline.phase03b1 import run_phase03b1
from sll_probabilistic_pipeline.utils import read_tsv, write_tsv

from ._runtime_fixture import REPO_ROOT, clone_phase03a_runtime


class Phase03B1PreflightTest(unittest.TestCase):
    def test_warning_or_fail_in_phase03a_runtime_blocks_phase03b1(self) -> None:
        cloned_runtime = clone_phase03a_runtime()
        validation_path = cloned_runtime / "audit" / "phase03_validation_summary.tsv"
        rows = read_tsv(validation_path)
        rows.append(
            {
                "check_id": "synthetic_warning",
                "status": "WARN",
                "severity": "warning",
                "source_surface": "synthetic",
                "source_row_key": "synthetic",
                "details": "synthetic warning for phase03b1 preflight block test",
            }
        )
        write_tsv(
            validation_path,
            rows,
            ["check_id", "status", "severity", "source_surface", "source_row_key", "details"],
        )

        manifest = run_phase03b1(
            repo_root=REPO_ROOT,
            phase03a_runtime=cloned_runtime,
            out_root=DEFAULT_RESULTS_ROOT,
            strict=True,
        )
        self.assertEqual(manifest["phase03b1_completion_decision"], PHASE03B1_BLOCKED_STATE)
        self.assertEqual(manifest["phase_status"], "phase03b1_blocked_pending_repaired_phase03a_direct_read")

    def test_superseded_phase03a_runtime_is_rejected(self) -> None:
        if not DEFAULT_PHASE03A_SUPERSEDED_RUNTIME.exists():
            self.skipTest("Superseded Phase03A runtime not present in this environment")

        manifest = run_phase03b1(
            repo_root=REPO_ROOT,
            phase03a_runtime=DEFAULT_PHASE03A_SUPERSEDED_RUNTIME,
            out_root=DEFAULT_RESULTS_ROOT,
            strict=True,
        )
        self.assertEqual(manifest["phase03b1_completion_decision"], PHASE03B1_BLOCKED_STATE)
        validation_rows = read_tsv(
            Path(manifest["runtime_root"]) / "audit" / "phase03b1_validation_summary.tsv"
        )
        indexed = {row["check_id"]: row for row in validation_rows}
        self.assertEqual(indexed["superseded_phase03a_runtime_not_used"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
