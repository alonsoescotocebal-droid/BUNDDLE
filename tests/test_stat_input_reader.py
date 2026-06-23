from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_rows


class StatInputReaderTest(unittest.TestCase):
    def test_dense_interpolated_provenance_survives(self) -> None:
        rows = phase01b_rows("stat_dense_data_provenance_long.tsv")
        self.assertTrue(rows)
        interpolated = next(row for row in rows if row["provenance_kind"] == "dense_interpolated")
        self.assertIn("is_interpolated", interpolated)
        self.assertIn("gate_or_status", interpolated)
        self.assertIn("source_time_left_h", interpolated)
        self.assertIn("source_time_right_h", interpolated)
        self.assertNotEqual(interpolated["trace_id"], "")

    def test_descriptive_output_carries_snapshot_and_window_delta_rows(self) -> None:
        rows = phase01b_rows("stat_descriptive_node_state_long.tsv")
        kinds = {row["descriptive_measure_type"] for row in rows}
        self.assertIn("snapshot_value", kinds)
        self.assertIn("window_delta", kinds)


if __name__ == "__main__":
    unittest.main()
