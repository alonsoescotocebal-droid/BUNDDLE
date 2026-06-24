from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_join_repair_rows


class JoinAdmissibilityContractTest(unittest.TestCase):
    def test_known_problem_pairs_are_resolved_with_expected_modes(self) -> None:
        rows = phase01b_join_repair_rows("join_admissibility_contract.tsv")
        indexed = {(row["left_surface"], row["right_surface"]): row for row in rows}
        self.assertEqual(
            indexed[("stat_descriptive_node_state_long.tsv", "kinetic_rate_primary_long.tsv")]["join_admissibility"],
            "projection_only",
        )
        self.assertEqual(
            indexed[
                ("stat_descriptive_node_state_long.tsv", "kinetic_temporal_coupling_primary_long.tsv")
            ]["join_admissibility"],
            "projection_only",
        )
        self.assertEqual(
            indexed[("growth_variable_identity_audit.tsv", "kinetic_growth_primary_long.tsv")]["join_admissibility"],
            "policy_lookup_only",
        )
        for row in rows:
            self.assertEqual(row["resolution_state"], "resolved")


if __name__ == "__main__":
    unittest.main()
