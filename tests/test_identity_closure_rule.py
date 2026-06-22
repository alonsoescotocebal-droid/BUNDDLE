from __future__ import annotations

import unittest

from sll_probabilistic_pipeline.standardize.join_identity import classify_identity_closure_state


class IdentityClosureRuleTest(unittest.TestCase):
    def test_missing_trace_is_internal_failure(self) -> None:
        growth_rows = [
            {
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_row_key": "",
                "source_column": "variable",
                "growth_value_type": "lnOD",
                "transformation_formula_if_known": "unknown_from_source",
            }
        ]
        acetate_rows = [
            {
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_row_key": "row1",
                "role_as_added_perturbator": "yes",
            }
        ]
        self.assertEqual(
            classify_identity_closure_state(growth_rows, acetate_rows),
            "internal_failure_localized",
        )

    def test_undetermined_added_role_is_external_validation_required(self) -> None:
        growth_rows = [
            {
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_row_key": "row1",
                "source_column": "variable",
                "growth_value_type": "raw_OD600",
                "transformation_formula_if_known": "not_applicable",
            }
        ]
        acetate_rows = [
            {
                "source_surface": "intermediate/analysis_view_observed.tsv",
                "source_row_key": "row2",
                "role_as_added_perturbator": "undetermined",
            }
        ]
        self.assertEqual(
            classify_identity_closure_state(growth_rows, acetate_rows),
            "external_validation_required",
        )


if __name__ == "__main__":
    unittest.main()
