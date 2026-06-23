from __future__ import annotations

import unittest

from ._runtime_fixture import phase01b_rows


class LagRunVsEdgeLagTest(unittest.TestCase):
    def test_all_four_lag_runs_are_present(self) -> None:
        rows = phase01b_rows("stat_pcmci_edge_long.tsv")
        self.assertTrue(rows)
        discovered = sorted({int(row["run_max_lag"]) for row in rows})
        self.assertEqual(discovered, [1, 2, 3, 4])

    def test_edge_lag_is_separate_and_bounded(self) -> None:
        rows = phase01b_rows("stat_pcmci_edge_long.tsv")
        self.assertTrue(any(int(row["edge_lag"]) != int(row["run_max_lag"]) for row in rows))
        self.assertTrue(all(int(row["edge_lag"]) <= int(row["run_max_lag"]) for row in rows))


if __name__ == "__main__":
    unittest.main()
