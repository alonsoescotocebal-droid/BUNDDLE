from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_audit_rows, phase03a_rows


class Phase03AForbiddenOutputsTest(unittest.TestCase):
    def test_forbidden_output_scan_is_clean(self) -> None:
        rows = phase03a_rows("phase03_forbidden_output_scan.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["present_yes_no"] == "no" for row in rows))

    def test_probability_tensor_remains_pre_posterior(self) -> None:
        rows = phase03a_rows("relation_probability_evidence_tensor.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["not_posterior_yes_no"] == "yes" for row in rows))
        self.assertTrue(all(row["not_causal_probability_yes_no"] == "yes" for row in rows))

    def test_validation_reports_probability_tensor_as_not_posterior(self) -> None:
        rows = phase03a_audit_rows("phase03_validation_summary.tsv")
        indexed = {row["check_id"]: row for row in rows}
        self.assertEqual(indexed["relation_probability_evidence_tensor_not_posterior"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
