from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_rows


class Phase03AKineticRealOnlyTest(unittest.TestCase):
    def test_kinetic_likelihood_surface_uses_real_only_only(self) -> None:
        rows = phase03a_rows("kinetic_likelihood_surface.tsv")
        data_rows = [row for row in rows if row["relation_anchor_id"]]
        self.assertTrue(data_rows)
        self.assertTrue(all(row["branch"] in {"", "real_only"} for row in data_rows))
        self.assertTrue(all(row["branch"] != "real_plus_interpolated" for row in data_rows))


if __name__ == "__main__":
    unittest.main()
