from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from experiments.event_conditioned_width_phase0.run_structural_falsification import (  # noqa: E402
    binding_verdict,
    explicit_global_reduction_check,
    explicit_site_grouped_tensor_unfolding,
    independent_exhaustive_audit,
    run_global_reduction_controls,
    tie_aware_headroom,
)
from experiments.event_conditioned_width_phase0.structural_core import (  # noqa: E402
    BooleanEvent,
    InteractionGraph,
    build_structural_tables,
    exhaustive_permutation_search,
    factorial_permutation_count,
    order_profile,
    synthetic_instance,
)


def _search_all(instance, tables):
    return {
        objective: exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective=objective,
            tables=tables,
        )
        for objective in ("event", "circuit", "joint")
    }


class StructuralFalsificationRunnerTests(unittest.TestCase):
    def test_explicit_full_tensor_reduction_controls(self) -> None:
        controls = run_global_reduction_controls()
        self.assertTrue(controls["passed"])
        self.assertEqual(len(controls["checks"]), 4)
        self.assertEqual(
            controls["checks"][0]["explicit_rank"],
            2,
        )
        internal = next(
            control
            for control in controls["checks"]
            if control["name"] == "internal_edge_does_not_increase_rank"
        )
        self.assertEqual(internal["crossing_edges"], 0)
        self.assertEqual(internal["edge_factor_rank"], 1)
        self.assertEqual(internal["explicit_rank"], internal["event_rank"])

    def test_nontrivial_event_rank_multiplies_crossing_bell_ranks(self) -> None:
        event = BooleanEvent.from_support(
            ["000", "010", "101", "111"], n=3
        )
        graph = InteractionGraph.from_edges(3, [(0, 1), (1, 2)])
        result = explicit_global_reduction_check(event, graph, 2, 0b011)
        self.assertEqual(result["event_rank"], 2)
        self.assertEqual(result["crossing_edges"], 1)
        self.assertEqual(result["edge_factor_rank"], 4)
        self.assertEqual(result["explicit_rank"], 8)
        self.assertTrue(result["passed"])

    def test_same_global_tensor_formula_holds_for_every_three_site_cut(self) -> None:
        event = BooleanEvent.from_support(
            ["000", "010", "101", "111"], n=3
        )
        graph = InteractionGraph.from_edges(3, [(0, 1), (1, 2)])
        for left_mask in range(1 << event.n):
            with self.subTest(left_mask=left_mask):
                result = explicit_global_reduction_check(
                    event, graph, 2, left_mask
                )
                self.assertTrue(result["passed"])

    def test_explicit_full_tensor_guard(self) -> None:
        event = BooleanEvent.from_support(["000", "111"], n=3)
        graph = InteractionGraph.from_edges(3, [(0, 1), (1, 2)])
        with self.assertRaisesRegex(ValueError, "above limit"):
            explicit_site_grouped_tensor_unfolding(
                event, graph, 2, 0b001, max_entries=100
            )

    def test_independent_pass_verifies_scores_ties_and_factorial_count(self) -> None:
        instance = synthetic_instance("anti_aligned", n=5, depth=2)
        tables = build_structural_tables(instance.event, instance.graph)
        searches = _search_all(instance, tables)

        audit = independent_exhaustive_audit(tables, instance.depth, searches)

        self.assertTrue(audit["passed"])
        self.assertEqual(
            audit["permutations_evaluated_independently"],
            factorial_permutation_count(5),
        )
        self.assertTrue(
            all(check["passed"] for check in audit["search_checks"].values())
        )

    def test_headroom_uses_complete_argmin_sets_not_first_retained_tie(self) -> None:
        instance = synthetic_instance("circuit_hard", n=5, depth=1)
        tables = build_structural_tables(instance.event, instance.graph)
        searches = _search_all(instance, tables)
        audit = independent_exhaustive_audit(tables, instance.depth, searches)
        headroom = tie_aware_headroom(audit)

        canonical_circuit_order = searches["circuit"].retained_optimal_orders[0]
        canonical_joint_score = order_profile(
            instance.event,
            instance.graph,
            instance.depth,
            canonical_circuit_order,
            tables=tables,
        ).max_joint_rank_product

        self.assertEqual(
            audit["circuit_optimal_set"]["optimal_order_count"],
            factorial_permutation_count(5),
        )
        self.assertGreater(
            canonical_joint_score,
            audit["circuit_optimal_set"]["best_joint_score"],
        )
        self.assertEqual(
            audit["circuit_optimal_set"]["best_joint_score"],
            audit["joint_optimum"]["best_score"],
        )
        self.assertEqual(headroom["ratio"], 1.0)
        self.assertFalse(headroom["strict_headroom"])
        self.assertTrue(headroom["tie_break_sensitive"])

    def test_binding_verdict_does_not_overclaim_the_proxy_witness(self) -> None:
        verdict = binding_verdict(
            [
                {
                    "exhaustive_audit": {"passed": True},
                    "collapse": {
                        "passed": True,
                        "explicit_checks": 3,
                        "explicit_checks_skipped": 1,
                    },
                }
            ],
            {"passed": True},
        )

        self.assertTrue(verdict["exhaustive_searches_independently_verified"])
        self.assertTrue(verdict["proxy_kronecker_rank_identity_verified"])
        self.assertTrue(
            verdict["global_site_grouped_tensor_reduction_established"]
        )
        self.assertTrue(
            verdict["natural_proxy_equals_linear_tt_rank_width_of_artificial_tensor"]
        )
        self.assertFalse(verdict["actual_circuit_unfolding_equivalence_established"])
        self.assertEqual(verdict["protocol_kill_gate"], "K6")
        self.assertFalse(verdict["a_star_novelty_survives"])

    def test_empty_run_cannot_report_success(self) -> None:
        verdict = binding_verdict([], {"passed": True})
        self.assertFalse(verdict["exhaustive_searches_independently_verified"])
        self.assertFalse(verdict["proxy_kronecker_rank_identity_verified"])
        self.assertFalse(verdict["global_site_grouped_tensor_reduction_established"])
        self.assertIsNone(verdict["protocol_kill_gate"])


if __name__ == "__main__":
    unittest.main()
