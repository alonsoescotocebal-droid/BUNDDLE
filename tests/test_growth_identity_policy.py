from __future__ import annotations

import unittest

from ._runtime_fixture import data_rows


class GrowthIdentityPolicyTest(unittest.TestCase):
    def test_growth_identity_fields_and_types(self) -> None:
        rows = data_rows("growth_variable_identity_audit.tsv")
        self.assertTrue(rows)
        fieldnames = set(rows[0].keys())
        self.assertIn("source_column", fieldnames)
        self.assertIn("source_row_key", fieldnames)

        stat_od600 = next(
            row
            for row in rows
            if row["source_layer"] == "statistical"
            and row["source_column"] == "assay_id"
            and row["raw_label"] == "OD600"
        )
        self.assertEqual(stat_od600["growth_value_type"], "raw_OD600")
        self.assertEqual(stat_od600["can_join_to_statistical_lnOD"], "no")

        stat_lnod = next(
            row
            for row in rows
            if row["source_layer"] == "statistical"
            and row["source_column"] == "variable"
            and row["raw_label"] == "lnOD"
        )
        self.assertEqual(stat_lnod["growth_value_type"], "lnOD")

        stat_lnabs = next(
            row
            for row in rows
            if row["source_layer"] == "statistical"
            and row["source_column"] == "assay_id"
            and row["raw_label"] == "ln(abs-abs0)"
        )
        self.assertEqual(stat_lnabs["growth_value_type"], "ln_abs_minus_abs0")
        self.assertEqual(stat_lnabs["can_join_to_statistical_lnOD"], "contextual_only")
        self.assertEqual(stat_lnabs["transformation_formula_if_known"], "unknown_from_source")

    def test_kinetic_growth_derivation_is_preserved(self) -> None:
        rows = data_rows("growth_variable_identity_audit.tsv")
        kinetic_formula = next(
            row
            for row in rows
            if row["source_layer"] == "kinetic"
            and row["source_column"] == "biomass_semantics"
        )
        self.assertEqual(kinetic_formula["growth_value_type"], "normalized_OD600")
        self.assertTrue(kinetic_formula["transformation_formula_if_known"].startswith("ln(OD600/"))


if __name__ == "__main__":
    unittest.main()

