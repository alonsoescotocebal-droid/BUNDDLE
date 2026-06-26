from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_audit_rows, phase03a_rows


class Phase03ALagPreservationTest(unittest.TestCase):
    def test_multilag_profile_preserves_run_max_lag_and_edge_lag(self) -> None:
        rows = phase03a_rows("multilag_temporal_profile_surface.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["run_max_lag"] != "" and row["edge_lag"] != "" for row in rows))
        self.assertTrue(all(row["no_global_lag_priority_yes_no"] == "yes" for row in rows))

    def test_validation_reports_no_global_lag_priority(self) -> None:
        rows = phase03a_audit_rows("phase03_validation_summary.tsv")
        indexed = {row["check_id"]: row for row in rows}
        self.assertEqual(indexed["run_max_lag_edge_lag_preserved"]["status"], "PASS")
        self.assertEqual(indexed["no_global_lag_priority"]["status"], "PASS")
        self.assertEqual(indexed["multilag_profile_preserved"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
