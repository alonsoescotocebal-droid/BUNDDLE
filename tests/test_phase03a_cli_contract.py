from __future__ import annotations

import subprocess
import sys
import unittest

from sll_probabilistic_pipeline.config import DEFAULT_RESULTS_ROOT, SUPPORTED_PHASES

from ._runtime_fixture import REPO_ROOT


class Phase03ACliContractTest(unittest.TestCase):
    def test_supported_phases_include_phase03a_but_not_plain_phase03(self) -> None:
        self.assertIn("phase03a", SUPPORTED_PHASES)
        self.assertNotIn("phase03", SUPPORTED_PHASES)

    def test_cli_requires_phase02_runtime(self) -> None:
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase03a",
            "--repo-root",
            str(REPO_ROOT),
            "--out-root",
            str(DEFAULT_RESULTS_ROOT),
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--phase02-runtime is required for phase03a", completed.stderr)


if __name__ == "__main__":
    unittest.main()
