from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_rows


class Phase03APosteriorSumToOneTest(unittest.TestCase):
    def test_probabilities_sum_to_one_per_relation(self) -> None:
        rows = phase03a_rows("posterior_relation_state.tsv")
        self.assertTrue(rows)
        for row in rows:
            total = (
                float(row["p_positive_support"])
                + float(row["p_negative_support"])
                + float(row["p_ambiguous_or_mixed"])
                + float(row["p_insufficient_or_uninformative"])
            )
            self.assertAlmostEqual(total, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
