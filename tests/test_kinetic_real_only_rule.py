from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_rows


class KineticRealOnlyRuleTest(unittest.TestCase):
    def test_primary_kinetic_outputs_use_real_only_only(self) -> None:
        for filename in (
            "kinetic_growth_primary_long.tsv",
            "kinetic_rate_primary_long.tsv",
            "kinetic_temporal_coupling_primary_long.tsv",
        ):
            rows = phase01b_rows(filename)
            self.assertTrue(rows)
            self.assertTrue(all(row["branch"] == "real_only" for row in rows))

    def test_disabled_branch_is_inventoried_but_not_used(self) -> None:
        rows = phase01b_rows("kinetic_disabled_branch_inventory.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["branch"] == "real_plus_interpolated" for row in rows))
        self.assertTrue(all(row["status"] == "excluded_by_canonical_rule" for row in rows))

    def test_empty_yield_surface_is_audited_legitimately(self) -> None:
        rows = phase01b_rows("input_empty_surface_audit.tsv")
        target = next(row for row in rows if row["source_surface"] == "95_audit/yield_pairs_handoff.tsv")
        self.assertEqual(target["empty_status"], "empty_legitimate")


if __name__ == "__main__":
    unittest.main()
