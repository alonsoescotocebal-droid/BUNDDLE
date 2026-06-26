from __future__ import annotations

import unittest

from ._runtime_fixture import phase02_audit_rows, phase02_rows


class Phase02LagPreservationTest(unittest.TestCase):
    def test_anchor_registry_preserves_run_max_lag_and_edge_lag(self) -> None:
        rows = phase02_rows("relation_anchor_registry.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["run_max_lag"] != "" and row["edge_lag"] != "" for row in rows))

    def test_validation_reports_no_global_lag_priority(self) -> None:
        rows = phase02_audit_rows("phase02_validation_summary.tsv")
        indexed = {row["check_id"]: row for row in rows}
        self.assertEqual(indexed["run_max_lag_edge_lag_preserved"]["status"], "PASS")
        self.assertEqual(indexed["no_global_lag_priority"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
