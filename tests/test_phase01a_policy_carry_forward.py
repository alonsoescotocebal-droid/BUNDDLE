from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_rows


class Phase01APolicyCarryForwardTest(unittest.TestCase):
    def test_policy_artifacts_are_present_and_marked_immutable(self) -> None:
        rows = phase01b_rows("phase01a_policy_carry_forward_audit.tsv")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["status"] == "present_and_usable" for row in rows))
        self.assertTrue(all(row["immutable_policy_yes_no"] == "yes" for row in rows))

    def test_growth_join_policy_is_carried_forward(self) -> None:
        rows = phase01b_rows("cross_layer_join_identity_policy.tsv")
        target = next(
            row
            for row in rows
            if row["canonical_component_id"] == "growth_node"
            and row["value_type_left"] == "lnOD"
            and row["value_type_right"] == "raw_OD600"
        )
        self.assertEqual(target["join_decision"], "forbidden")


if __name__ == "__main__":
    unittest.main()
