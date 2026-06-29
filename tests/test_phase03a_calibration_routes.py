from __future__ import annotations

import csv
from pathlib import Path
import unittest

from sll_probabilistic_pipeline.phase03a import _build_temporal_pcmci_calibration_surface

from ._runtime_fixture import build_phase03a_runtime, phase03a_audit_rows, phase03a_rows


class Phase03ACalibrationRoutesTest(unittest.TestCase):
    def test_runtime_routes_are_declared_and_allowed(self) -> None:
        rows = phase03a_rows("temporal_pcmci_calibration_surface.tsv")
        routes = {row["calibration_route"] for row in rows}
        self.assertTrue(routes)
        self.assertTrue(routes.issubset(
            {
                "empirical_rank_by_run_max_lag",
                "empirical_rank_pooled_lags",
                "conservative_logistic_fallback",
                "missing_or_invalid_q_value",
            }
        ))

    def test_small_synthetic_dataset_uses_fallback_route(self) -> None:
        stat_rows = [
            {
                "relation_anchor_id": f"anchor_{idx}",
                "run_max_lag": "1",
                "edge_lag": "1",
                "abs_evidence_score": f"{0.1 * (idx + 1):.12f}",
                "signed_evidence_score": f"{0.1 * (idx + 1):.12f}",
                "temporal_signal_direction": "positive",
                "calibration_eligible_yes_no": "yes",
            }
            for idx in range(3)
        ]
        rows, _ = _build_temporal_pcmci_calibration_surface(stat_rows)
        self.assertTrue(rows)
        self.assertTrue(all(row["calibration_route"] == "conservative_logistic_fallback" for row in rows))

    def test_probability_calibration_audit_row_counts_match_temporal_surface(self) -> None:
        runtime_dir, _ = build_phase03a_runtime()
        temporal_rows = phase03a_rows("temporal_pcmci_calibration_surface.tsv")
        expected_counts: dict[str, int] = {}
        for row in temporal_rows:
            expected_counts[row["run_max_lag"]] = expected_counts.get(row["run_max_lag"], 0) + 1

        audit_path = runtime_dir / "data" / "probability_calibration_audit.tsv"
        with audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
            audit_rows = list(csv.DictReader(handle, delimiter="\t"))
        actual_counts = {
            row["calibration_group"]: int(row["row_count"])
            for row in audit_rows
            if row["audit_scope"] == "run_max_lag"
        }
        self.assertEqual(actual_counts, expected_counts)

    def test_validation_reports_calibration_audit_row_counts_match(self) -> None:
        rows = phase03a_audit_rows("phase03_validation_summary.tsv")
        indexed = {row["check_id"]: row for row in rows}
        self.assertEqual(indexed["probability_calibration_audit_row_counts_match"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
