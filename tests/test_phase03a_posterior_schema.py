from __future__ import annotations

import unittest

from ._runtime_fixture import phase03a_rows


class Phase03APosteriorSchemaTest(unittest.TestCase):
    REQUIRED_COLUMNS = {
        "relation_anchor_id",
        "target_component_id",
        "perturbator_component_id",
        "scenario_canonical",
        "condition_role",
        "condition_id",
        "replicate",
        "window_label",
        "run_max_lag",
        "edge_lag",
        "calibration_route",
        "calibration_status",
        "qc_blocker_status",
        "semantic_compatibility_status",
        "p_positive_support",
        "p_negative_support",
        "p_ambiguous_or_mixed",
        "p_insufficient_or_uninformative",
        "posterior_state_argmax",
        "posterior_entropy",
        "probability_limitations_flag",
        "not_causal_probability_yes_no",
        "not_qa_answer_yes_no",
        "not_network_topology_yes_no",
        "not_final_decision_yes_no",
        "trace_id",
    }

    def test_posterior_schema_is_complete(self) -> None:
        rows = phase03a_rows("posterior_relation_state.tsv")
        self.assertTrue(rows)
        self.assertTrue(self.REQUIRED_COLUMNS.issubset(rows[0].keys()))
        self.assertTrue(all(row["not_causal_probability_yes_no"] == "yes" for row in rows))
        self.assertTrue(all(row["not_qa_answer_yes_no"] == "yes" for row in rows))
        self.assertTrue(all(row["not_network_topology_yes_no"] == "yes" for row in rows))
        self.assertTrue(all(row["not_final_decision_yes_no"] == "yes" for row in rows))


if __name__ == "__main__":
    unittest.main()
