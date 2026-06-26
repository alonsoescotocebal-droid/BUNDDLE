from __future__ import annotations

import unittest

from ._runtime_fixture import phase02_rows


class Phase02JoinContractConsumptionTest(unittest.TestCase):
    def test_phase02_join_contract_is_consumed(self) -> None:
        rows = phase02_rows("phase02_join_contract_consumption_audit.tsv")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["actual_consumption_status"] == "pass" for row in rows))
        self.assertTrue(all(row["contract_resolution_state"] == "resolved" for row in rows))
        self.assertTrue(all(row["admissibility_resolution_state"] == "resolved" for row in rows))
        modes = {row["phase02_consumption_mode"] for row in rows}
        self.assertIn("deduplicate_lag_invariant_descriptive_then_project_to_kinetic_component_context", modes)
        self.assertIn("identity_policy_lookup_only_do_not_join_as_measurement", modes)
        admissibility = {
            (row["left_surface"], row["right_surface"]): row["join_admissibility"]
            for row in rows
        }
        self.assertEqual(
            admissibility[("stat_descriptive_node_state_long.tsv", "kinetic_rate_primary_long.tsv")],
            "projection_only",
        )
        self.assertEqual(
            admissibility[("stat_descriptive_node_state_long.tsv", "kinetic_temporal_coupling_primary_long.tsv")],
            "projection_only",
        )
        self.assertEqual(
            admissibility[("growth_variable_identity_audit.tsv", "kinetic_growth_primary_long.tsv")],
            "policy_lookup_only",
        )


if __name__ == "__main__":
    unittest.main()
