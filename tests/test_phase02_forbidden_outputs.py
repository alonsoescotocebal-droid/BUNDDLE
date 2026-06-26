from __future__ import annotations

import unittest

from ._runtime_fixture import phase02_rows


class Phase02ForbiddenOutputsTest(unittest.TestCase):
    def test_forbidden_output_scan_is_clean(self) -> None:
        rows = phase02_rows("phase02_forbidden_output_scan.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["present_yes_no"] == "no" for row in rows))

    def test_relation_evidence_tensor_has_no_forbidden_columns(self) -> None:
        rows = phase02_rows("relation_evidence_tensor.tsv")
        self.assertTrue(rows)
        forbidden = {
            "posterior_probability",
            "P_signal",
            "P_state",
            "causal_probability",
            "final_score",
            "qa_answer_state",
            "network_degree",
            "final_go_no_go",
        }
        self.assertTrue(forbidden.isdisjoint(rows[0].keys()))


if __name__ == "__main__":
    unittest.main()
