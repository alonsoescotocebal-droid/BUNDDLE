from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE02_REBUILT_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE03A_REPO_OUTPUT_REJECTION_CODE,
)
from sll_probabilistic_pipeline.paths import Phase03APathError
from sll_probabilistic_pipeline.phase03a import run_phase03a

from ._runtime_fixture import REPO_ROOT, build_phase03a_runtime


class Phase03APathResolutionTest(unittest.TestCase):
    def test_out_root_inside_repo_is_rejected(self) -> None:
        with self.assertRaises(Phase03APathError) as ctx:
            run_phase03a(
                repo_root=REPO_ROOT,
                phase02_runtime=DEFAULT_PHASE02_REBUILT_RUNTIME,
                out_root=REPO_ROOT,
                strict=True,
            )
        self.assertEqual(ctx.exception.code, PHASE03A_REPO_OUTPUT_REJECTION_CODE)

    def test_runtime_root_is_created_under_external_results_with_required_prefix(self) -> None:
        runtime_dir, manifest = build_phase03a_runtime()
        self.assertTrue(runtime_dir.exists())
        self.assertTrue(str(runtime_dir).startswith(str(DEFAULT_RESULTS_ROOT)))
        self.assertTrue(runtime_dir.name.startswith("SLL_PHASE03A_PROBABILISTIC_CALIBRATION_"))
        self.assertEqual(Path(manifest["runtime_root"]), runtime_dir)


if __name__ == "__main__":
    unittest.main()
