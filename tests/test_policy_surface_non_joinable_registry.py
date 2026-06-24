from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_join_repair_rows


class PolicySurfaceNonJoinableRegistryTest(unittest.TestCase):
    def test_growth_identity_policy_surface_is_registered_as_non_joinable_measurement(self) -> None:
        rows = phase01b_join_repair_rows("policy_surface_non_joinable_registry.tsv")
        row = next(row for row in rows if row["surface_name"] == "growth_variable_identity_audit.tsv")
        self.assertEqual(row["non_joinable_as_measurement"], "yes")
        self.assertEqual(row["allowed_usage"], "policy_lookup_only")


if __name__ == "__main__":
    unittest.main()
