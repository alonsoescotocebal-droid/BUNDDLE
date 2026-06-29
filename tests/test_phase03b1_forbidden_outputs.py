from __future__ import annotations

import unittest

from ._runtime_fixture import build_phase03b1_runtime, phase03b1_rows


class Phase03B1ForbiddenOutputsTest(unittest.TestCase):
    def test_forbidden_output_scan_is_clean(self) -> None:
        rows = phase03b1_rows("phase03b1_forbidden_output_scan.tsv")
        self.assertTrue(rows)
        self.assertTrue(all(row["present_yes_no"] == "no" for row in rows))

    def test_final_outputs_remain_absent(self) -> None:
        runtime_dir, _ = build_phase03b1_runtime()
        self.assertFalse((runtime_dir / "data" / "final_machine_readable_consistency_audit.tsv").exists())
        self.assertFalse((runtime_dir / "data" / "final_static_release_decision.json").exists())

    def test_q21_q22_remain_deferred(self) -> None:
        rows = phase03b1_rows("runtime_question_answer_matrix.tsv")
        indexed = {row["question_id"]: row for row in rows}
        for question_id in ("Q21", "Q22"):
            row = indexed[question_id]
            self.assertEqual(row["answer_status"], "external_validation_required")
            self.assertEqual(row["closure_ready_yes_no"], "no")
            self.assertEqual(row["not_final_decision_yes_no"], "yes")


if __name__ == "__main__":
    unittest.main()
