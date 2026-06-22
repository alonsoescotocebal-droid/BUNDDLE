from __future__ import annotations

import unittest

from ._runtime_fixture import data_rows


class ComponentAliasRegistryTest(unittest.TestCase):
    def test_required_aliases_exist(self) -> None:
        rows = data_rows("canonical_component_alias_registry.tsv")
        self.assertTrue(rows)
        fieldnames = set(rows[0].keys())
        self.assertIn("raw_label", fieldnames)
        self.assertIn("canonical_component_id", fieldnames)
        self.assertIn("source_column", fieldnames)

        def has_alias(raw_label: str, canonical: str) -> bool:
            return any(
                row["raw_label"] == raw_label and row["canonical_component_id"] == canonical
                for row in rows
            )

        self.assertTrue(has_alias("Acetic acid", "acetate_gL"))
        self.assertTrue(has_alias("acetic acid", "acetate_gL"))
        self.assertTrue(has_alias("acetic_acid", "acetate_gL"))
        self.assertTrue(has_alias("OD600", "growth_node"))
        self.assertTrue(has_alias("lnOD", "growth_node"))

    def test_acetate_registry_flags_dual_role_capacity(self) -> None:
        rows = data_rows("canonical_component_alias_registry.tsv")
        acetate_rows = [row for row in rows if row["canonical_component_id"] == "acetate_gL"]
        self.assertTrue(acetate_rows)
        self.assertTrue(
            any(row["can_be_added_perturbator_when_test_delta_exists"] == "yes" for row in acetate_rows)
        )


if __name__ == "__main__":
    unittest.main()

