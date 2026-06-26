from __future__ import annotations

import subprocess
import sys
import unittest

from sll_probabilistic_pipeline.config import DEFAULT_PHASE02_REBUILT_RUNTIME, DEFAULT_RESULTS_ROOT

from ._runtime_fixture import REPO_ROOT


class Phase03ANoRawRootsTest(unittest.TestCase):
    def test_cli_rejects_stat_and_kin_roots_for_phase03a(self) -> None:
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
        self.assertIn("not accepted for phase03a", completed.stderr)

    def test_cli_rejects_phase01b_runtime_for_phase03a(self) -> None:
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
            "--phase01b-runtime",
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
        self.assertIn("--phase01b-runtime is not accepted for phase03a", completed.stderr)


if __name__ == "__main__":
    unittest.main()
