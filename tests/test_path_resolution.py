from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import (
    DEFAULT_KIN_ROOT,
    DEFAULT_RESULTS_ROOT,
    DEFAULT_STAT_ROOT,
    PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX,
    PHASE01B_REPO_OUTPUT_REJECTION_CODE,
)
from sll_probabilistic_pipeline.paths import Phase01BPathError
from sll_probabilistic_pipeline.phase01b import run_phase01b
from sll_probabilistic_pipeline.phase01b_join_repair import run_phase01b_join_repair

from ._runtime_fixture import APPROVED_PHASE01B_RUNTIME, REPO_ROOT, build_phase01b_join_repair_runtime, build_phase01b_runtime


class PathResolutionTest(unittest.TestCase):
    def test_out_root_inside_repo_is_rejected(self) -> None:
        with self.assertRaises(Phase01BPathError) as ctx:
            run_phase01b(
                repo_root=REPO_ROOT,
                stat_root=DEFAULT_STAT_ROOT,
                kin_root=DEFAULT_KIN_ROOT,
                out_root=REPO_ROOT,
                strict=True,
            )
        self.assertEqual(ctx.exception.code, PHASE01B_REPO_OUTPUT_REJECTION_CODE)

    def test_out_root_outside_allowed_results_root_is_rejected(self) -> None:
        outside = Path(r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\outside_phase01b_results")
        with self.assertRaises(Phase01BPathError) as ctx:
            run_phase01b(
                repo_root=REPO_ROOT,
                stat_root=DEFAULT_STAT_ROOT,
                kin_root=DEFAULT_KIN_ROOT,
                out_root=outside,
                strict=True,
            )
        self.assertEqual(ctx.exception.code, "PHASE01B_OUTPUT_ROOT_OUTSIDE_ALLOWED_RESULTS_ROOT")

    def test_runtime_root_is_created_under_external_results_with_required_prefix(self) -> None:
        runtime_dir, manifest = build_phase01b_runtime()
        self.assertTrue(runtime_dir.exists())
        self.assertTrue(str(runtime_dir).startswith(str(DEFAULT_RESULTS_ROOT)))
        self.assertTrue(runtime_dir.name.startswith("SLL_PHASE01B_NORMALIZED_INPUT_READER_"))
        self.assertEqual(Path(manifest["runtime_root"]), runtime_dir)

    def test_join_repair_out_root_inside_repo_is_rejected(self) -> None:
        with self.assertRaises(Phase01BPathError) as ctx:
            run_phase01b_join_repair(
                repo_root=REPO_ROOT,
                phase01b_runtime=APPROVED_PHASE01B_RUNTIME,
                out_root=REPO_ROOT,
                strict=True,
            )
        self.assertEqual(ctx.exception.code, PHASE01B_REPO_OUTPUT_REJECTION_CODE)

    def test_join_repair_runtime_root_is_created_under_external_results_with_required_prefix(self) -> None:
        runtime_dir, manifest = build_phase01b_join_repair_runtime()
        self.assertTrue(runtime_dir.exists())
        self.assertTrue(str(runtime_dir).startswith(str(DEFAULT_RESULTS_ROOT)))
        self.assertTrue(runtime_dir.name.startswith(PHASE01B_JOIN_REPAIR_RUNTIME_PREFIX))
        self.assertEqual(Path(manifest["runtime_root"]), runtime_dir)


if __name__ == "__main__":
    unittest.main()
