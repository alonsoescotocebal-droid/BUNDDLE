from __future__ import annotations

import unittest
from pathlib import Path

from sll_probabilistic_pipeline.config import DEFAULT_RESULTS_ROOT
from sll_probabilistic_pipeline.paths import Phase01BPathError, resolve_phase01b_join_repair_paths
from sll_probabilistic_pipeline.phase01b_join_repair import _preflight_input_runtime
from sll_probabilistic_pipeline.utils import read_json, read_tsv

from ._runtime_fixture import APPROVED_PHASE01B_RUNTIME, REPO_ROOT


class Phase01BJoinRepairPreflightTest(unittest.TestCase):
    def test_phase01b_runtime_outside_allowed_results_root_is_rejected(self) -> None:
        outside_runtime = Path(r"D:\INTERDEPDNDENCIA_ARTIGOS_ANA\outside_phase01b_runtime")
        with self.assertRaises(Phase01BPathError) as ctx:
            resolve_phase01b_join_repair_paths(
                repo_root=REPO_ROOT,
                phase01b_runtime=outside_runtime,
                out_root=DEFAULT_RESULTS_ROOT,
            )
        self.assertEqual(ctx.exception.code, "PHASE01B_RUNTIME_OUTSIDE_ALLOWED_RESULTS_ROOT")

    def test_preflight_rejects_disallowed_warning_rows(self) -> None:
        resolved = resolve_phase01b_join_repair_paths(
            repo_root=REPO_ROOT,
            phase01b_runtime=APPROVED_PHASE01B_RUNTIME,
            out_root=DEFAULT_RESULTS_ROOT,
        )
        input_manifest = read_json(resolved.input_manifest)
        input_validation_rows = read_tsv(resolved.input_validation_summary)
        input_validation_rows.append(
            {
                "check_id": "unexpected_warning",
                "status": "WARN",
                "severity": "warning",
                "source_surface": "synthetic",
                "source_row_key": "synthetic",
                "details": "synthetic_disallowed_warning",
            }
        )
        with self.assertRaises(RuntimeError):
            _preflight_input_runtime(
                resolved=resolved,
                input_manifest=input_manifest,
                input_validation_rows=input_validation_rows,
                strict=True,
            )

    def test_preflight_rejects_error_level_failures(self) -> None:
        resolved = resolve_phase01b_join_repair_paths(
            repo_root=REPO_ROOT,
            phase01b_runtime=APPROVED_PHASE01B_RUNTIME,
            out_root=DEFAULT_RESULTS_ROOT,
        )
        input_manifest = read_json(resolved.input_manifest)
        input_validation_rows = read_tsv(resolved.input_validation_summary)
        input_validation_rows.append(
            {
                "check_id": "synthetic_failure",
                "status": "FAIL",
                "severity": "error",
                "source_surface": "synthetic",
                "source_row_key": "synthetic",
                "details": "synthetic_fail_row",
            }
        )
        with self.assertRaises(RuntimeError):
            _preflight_input_runtime(
                resolved=resolved,
                input_manifest=input_manifest,
                input_validation_rows=input_validation_rows,
                strict=True,
            )


if __name__ == "__main__":
    unittest.main()
