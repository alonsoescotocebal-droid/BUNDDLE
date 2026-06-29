from __future__ import annotations

import subprocess
import sys
import unittest

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE03A_REPAIRED_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    SUPPORTED_PHASES,
)

from ._runtime_fixture import REPO_ROOT


class Phase03B1CliContractTest(unittest.TestCase):
    def test_supported_phases_include_phase03b1_but_not_phase03b_or_phase04(self) -> None:
        self.assertIn("phase03b1", SUPPORTED_PHASES)
        self.assertNotIn("phase03b", SUPPORTED_PHASES)
        self.assertNotIn("phase03", SUPPORTED_PHASES)
        self.assertNotIn("phase04", SUPPORTED_PHASES)

    def test_cli_requires_phase03a_runtime(self) -> None:
        command = [
            sys.executable,
            "-m",
            "sll_probabilistic_pipeline.cli",
            "--phase",
            "phase03b1",
            "--repo-root",
            str(REPO_ROOT),
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
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--phase03a-runtime is required for phase03b1", completed.stderr)

    def test_cli_requires_strict(self) -> None:
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
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--strict is required for phase03b1", completed.stderr)

    def test_cli_rejects_phase02_runtime(self) -> None:
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
            "--phase02-runtime",
            "synthetic",
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
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--phase02-runtime is not accepted for phase03b1", completed.stderr)


if __name__ == "__main__":
    unittest.main()
