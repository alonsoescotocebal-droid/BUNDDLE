from __future__ import annotations

import unittest

from ._runtime_fixture import phase02_rows


class Phase02KineticRealOnlyTest(unittest.TestCase):
    def test_kinetic_evidence_surfaces_use_real_only_only(self) -> None:
        filenames = (
            "kinetic_growth_evidence_intake.tsv",
            "kinetic_rate_evidence_intake.tsv",
            "kinetic_temporal_coupling_evidence_intake.tsv",
            "kinetic_yield_evidence_intake.tsv",
        )
        for filename in filenames:
            rows = phase02_rows(filename)
            self.assertTrue(all(row["branch"] in {"", "real_only"} for row in rows), filename)
            self.assertTrue(all(row["branch"] != "real_plus_interpolated" for row in rows), filename)


if __name__ == "__main__":
    unittest.main()
