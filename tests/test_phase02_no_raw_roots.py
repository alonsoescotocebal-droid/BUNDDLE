from __future__ import annotations

import subprocess
import sys
import unittest

from sll_probabilistic_pipeline.config import DEFAULT_PHASE01B_REBUILT_RUNTIME, DEFAULT_RESULTS_ROOT

from ._runtime_fixture import REPO_ROOT


class Phase02NoRawRootsTest(unittest.TestCase):
    def test_cli_rejects_stat_and_kin_roots_for_phase02(self) -> None:
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
            "--stat-root",
            "forbidden",
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not accepted for phase02", completed.stderr)


if __name__ == "__main__":
    unittest.main()
