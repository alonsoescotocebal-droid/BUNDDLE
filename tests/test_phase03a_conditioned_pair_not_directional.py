from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_rows


class Phase03AConditionedPairDirectionalTest(unittest.TestCase):
    def test_conditioned_pair_surface_remains_non_directional(self) -> None:
        rows = phase03a_rows("conditioned_pair_probability_evidence_surface.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["directional_support_allowed_yes_no"] == "no" for row in rows))
        self.assertTrue(all(float(row["positive_direction_mass"]) == 0.0 for row in rows))
        self.assertTrue(all(float(row["negative_direction_mass"]) == 0.0 for row in rows))


if __name__ == "__main__":
    unittest.main()
