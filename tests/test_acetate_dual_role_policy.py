from __future__ import annotations

import unittest

from ._runtime_fixture import data_rows


class AcetateDualRolePolicyTest(unittest.TestCase):
    def test_test_condition_keeps_basal_and_added_roles(self) -> None:
        rows = data_rows("acetate_dual_role_audit.tsv")
        target = next(
            row
            for row in rows
            if row["condition_id"] == "Leachates+Inhibitors All" and row["scenario"] == "MIX_MAX"
        )
        self.assertEqual(target["role_as_basal_axis"], "yes")
        self.assertEqual(target["role_as_added_perturbator"], "yes")
        self.assertEqual(target["basis_for_added_perturbator"], "concentration_differs_from_ctrl")
        self.assertEqual(target["ctrl_reference_available"], "yes")
        self.assertEqual(target["test_delta_available"], "yes")

    def test_control_condition_is_not_marked_as_added_perturbator(self) -> None:
        rows = data_rows("acetate_dual_role_audit.tsv")
        control = next(
            row
            for row in rows
            if row["condition_id"] == "Leachates+Inhibitors_Control" and row["scenario"] == "MAX"
        )
        self.assertEqual(control["role_as_basal_axis"], "yes")
        self.assertEqual(control["role_as_added_perturbator"], "no")
        self.assertEqual(control["basis_for_added_perturbator"], "not_applicable")


if __name__ == "__main__":
    unittest.main()

