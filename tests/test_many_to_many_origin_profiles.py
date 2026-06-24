from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_join_repair_rows


class ManyToManyOriginProfilesTest(unittest.TestCase):
    def test_descriptive_pairs_preserve_measured_broad_key_cartesian_expansion(self) -> None:
        rows = phase01b_join_repair_rows("many_to_many_origin_diagnostic.tsv")
        indexed = {(row["left_surface"], row["right_surface"]): row for row in rows}
        for right_surface in ("kinetic_rate_primary_long.tsv", "kinetic_temporal_coupling_primary_long.tsv"):
            row = indexed[("stat_descriptive_node_state_long.tsv", right_surface)]
            self.assertEqual(row["max_cartesian_expansion_current"], "1008")
            self.assertEqual(row["left_max_multiplicity_current"], "168")
            self.assertEqual(row["right_max_multiplicity_current"], "6")

    def test_growth_policy_misuse_cartesian_expansion_is_profiled(self) -> None:
        rows = phase01b_join_repair_rows("many_to_many_origin_diagnostic.tsv")
        row = next(
            row
            for row in rows
            if row["left_surface"] == "growth_variable_identity_audit.tsv"
            and row["right_surface"] == "kinetic_growth_primary_long.tsv"
        )
        self.assertEqual(row["max_cartesian_expansion_current"], "21648")
        self.assertEqual(row["join_admissibility"], "policy_lookup_only")

    def test_descriptive_lag_invariant_duplicates_are_exactly_four_runs_each(self) -> None:
        rows = phase01b_join_repair_rows("lag_invariant_duplicate_origin_audit.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["duplicate_count"] == "4" for row in rows))
        self.assertTrue(all(row["distinct_run_max_lag_count"] == "4" for row in rows))
        self.assertTrue(all(row["run_max_lag_values"] == "1;2;3;4" for row in rows))


if __name__ == "__main__":
    unittest.main()
