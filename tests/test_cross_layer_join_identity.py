from __future__ import annotations

import unittest

from ._runtime_fixture import data_rows


class CrossLayerJoinIdentityTest(unittest.TestCase):
    def test_growth_join_rules_preserve_value_type(self) -> None:
        rows = data_rows("cross_layer_join_identity_policy.tsv")
        forbidden = next(
            row
            for row in rows
            if row["canonical_component_id"] == "growth_node"
            and row["value_type_left"] == "lnOD"
            and row["value_type_right"] == "raw_OD600"
        )
        self.assertEqual(forbidden["join_decision"], "forbidden")

        contextual = next(
            row
            for row in rows
            if row["canonical_component_id"] == "growth_node"
            and row["value_type_left"] == "lnOD"
            and row["value_type_right"] == "normalized_OD600"
        )
        self.assertEqual(contextual["join_decision"], "contextual_only")

    def test_acetate_join_rules_preserve_role_scope(self) -> None:
        rows = data_rows("cross_layer_join_identity_policy.tsv")
        acetate = next(
            row
            for row in rows
            if row["canonical_component_id"] == "acetate_gL"
            and row["evidence_scope_left"] == "added_perturbator_component"
        )
        self.assertEqual(acetate["join_decision"], "contextual_only")
        self.assertEqual(acetate["raw_measure_identity"], "no")


if __name__ == "__main__":
    unittest.main()

