from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_representation_sweep import (  # noqa: E402
    case_matrix,
    summarize_cases,
)


def _row(representation: str, order: str, flops: int, peak: int) -> dict:
    return {
        "representation": representation,
        "order_name": order,
        "order": [0, 1],
        "event_max_bond_rank": 2,
        "path": {"estimated_flops": flops, "peak_elements": peak},
    }


class RepresentationSweepTests(unittest.TestCase):
    def test_fixed_development_matrix(self) -> None:
        matrix = case_matrix()
        self.assertEqual(len(matrix), 48)
        self.assertEqual(len({row["case_id"] for row in matrix}), 48)
        self.assertEqual({row["qubits"] for row in matrix}, {5, 6, 7, 8})
        self.assertEqual({row["depth"] for row in matrix}, {1, 2})
        self.assertEqual(
            {row["family"] for row in matrix}, {"path", "cycle", "star", "random"}
        )
        self.assertEqual(
            {row["graph_seed"] for row in matrix if row["family"] == "random"},
            {260902, 260903, 260904},
        )

    def test_summary_pairs_orders_and_compares_best_orders(self) -> None:
        case = {
            "case_id": "toy",
            "family": "path",
            "graph_seed": None,
            "qubits": 2,
            "depth": 1,
            "screen": {
                "semantic_audits": [{"passed": True}],
                "rows": [
                    _row("rank_minimal_support_mpo", "natural", 10, 5),
                    _row("local_mis_plus_cardinality", "natural", 30, 10),
                    _row("rank_minimal_support_mpo", "reverse", 20, 8),
                    _row("local_mis_plus_cardinality", "reverse", 24, 12),
                ],
            },
        }
        summary = summarize_cases([case])
        self.assertTrue(summary["all_semantic_audits_passed"])
        self.assertEqual(summary["paired_order_comparison_count"], 2)
        self.assertAlmostEqual(summary["paired_order_flop_ratio"]["median"], 2.1)
        self.assertAlmostEqual(
            summary["best_order_per_representation_flop_ratio"]["median"], 2.4
        )
        self.assertEqual(
            summary["best_order_flop_winners"]["rank_minimal_support_mpo"], 1
        )


if __name__ == "__main__":
    unittest.main()
