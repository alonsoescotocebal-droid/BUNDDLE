from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_PHASE01B_REBUILT_RUNTIME,
    DEFAULT_RESULTS_ROOT,
    PHASE02_REPO_OUTPUT_REJECTION_CODE,
)
from sll_probabilistic_pipeline.paths import Phase02PathError
from sll_probabilistic_pipeline.phase02 import run_phase02

from ._runtime_fixture import REPO_ROOT, build_phase02_runtime


class Phase02PathResolutionTest(unittest.TestCase):
    def test_out_root_inside_repo_is_rejected(self) -> None:
        with self.assertRaises(Phase02PathError) as ctx:
            run_phase02(
                repo_root=REPO_ROOT,
                phase01b_runtime=DEFAULT_PHASE01B_REBUILT_RUNTIME,
                out_root=REPO_ROOT,
                strict=True,
            )
        self.assertEqual(ctx.exception.code, PHASE02_REPO_OUTPUT_REJECTION_CODE)

    def test_runtime_root_is_created_under_external_results_with_required_prefix(self) -> None:
        runtime_dir, manifest = build_phase02_runtime()
        self.assertTrue(runtime_dir.exists())
        self.assertTrue(str(runtime_dir).startswith(str(DEFAULT_RESULTS_ROOT)))
        self.assertTrue(runtime_dir.name.startswith("SLL_PHASE02_RELATION_EVIDENCE_INTAKE_"))
        self.assertEqual(Path(manifest["runtime_root"]), runtime_dir)


if __name__ == "__main__":
    unittest.main()
