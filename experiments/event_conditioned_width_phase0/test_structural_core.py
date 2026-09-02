from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from structural_core import (  # noqa: E402
    BooleanEvent,
    ImplicitProxyKroneckerUnfolding,
    InteractionGraph,
    audit_joint_rank_collapse,
    build_structural_tables,
    event_rank_table,
    event_unfolding_rank,
    exact_integer_matrix_rank,
    exhaustive_permutation_search,
    factorial_permutation_count,
    order_profile,
    paired_equality_support,
    synthetic_instance,
)


class StructuralCoreTests(unittest.TestCase):
    def test_fraction_free_rank_is_exact_over_rationals(self) -> None:
        self.assertEqual(exact_integer_matrix_rank([[1, 1], [1, 1]]), 1)
        self.assertEqual(exact_integer_matrix_rank([[1, 2], [2, 4], [3, 7]]), 2)
        self.assertEqual(exact_integer_matrix_rank([[0, 0], [0, 0]]), 0)

    def test_boolean_event_validation(self) -> None:
        event = BooleanEvent.from_support(["000", (1, 0, 1)])
        self.assertEqual(event.n, 3)
        self.assertEqual(event.support, ((0, 0, 0), (1, 0, 1)))
        with self.assertRaises(ValueError):
            BooleanEvent.from_support([], n=None)
        with self.assertRaises(ValueError):
            BooleanEvent.from_support(["00", "00"])
        with self.assertRaises(ValueError):
            BooleanEvent.from_support(["012"])

    def test_paired_event_rank_depends_on_order(self) -> None:
        event = BooleanEvent.from_support(paired_equality_support(6), n=6)
        graph = InteractionGraph.from_edges(6, [])
        paired = order_profile(event, graph, 0, (0, 1, 2, 3, 4, 5))
        split = order_profile(event, graph, 0, (0, 2, 4, 1, 3, 5))
        self.assertEqual(paired.max_event_rank, 2)
        self.assertEqual(split.max_event_rank, 8)

    def test_rank_table_uses_transpose_symmetry(self) -> None:
        event = BooleanEvent.from_support(["0000", "0011", "1100"], n=4)
        ranks = event_rank_table(event)
        full = (1 << event.n) - 1
        for mask, rank in enumerate(ranks):
            self.assertEqual(rank, ranks[full ^ mask])
            self.assertEqual(rank, event_unfolding_rank(event, mask))

    def test_natural_joint_profile(self) -> None:
        event = BooleanEvent.from_support(["000", "111"], n=3)
        graph = InteractionGraph.from_edges(3, [(0, 1), (1, 2)])
        profile = order_profile(event, graph, 2, (0, 1, 2))
        self.assertEqual([cut.event_rank for cut in profile.cuts], [2, 2])
        self.assertEqual([cut.crossing_edges for cut in profile.cuts], [1, 1])
        self.assertEqual([cut.circuit_cut_term for cut in profile.cuts], [4, 4])
        self.assertEqual([cut.joint_rank_product for cut in profile.cuts], [32, 32])
        self.assertEqual(profile.max_joint_rank_product, 32)
        self.assertEqual(profile.joint_J, 5.0)

    def test_implicit_product_collapse_materializes_for_small_case(self) -> None:
        event = BooleanEvent.from_support(["0000", "0011", "1100", "1111"], n=4)
        graph = InteractionGraph.from_edges(4, [(0, 1), (1, 2), (2, 3)])
        audit = audit_joint_rank_collapse(
            event,
            graph,
            1,
            (0, 1, 2, 3),
            max_explicit_entries=100_000,
        )
        self.assertTrue(audit.passed)
        self.assertEqual(audit.explicit_checks, 3)
        for cut in audit.cuts:
            self.assertEqual(cut.predicted_joint_rank, cut.implicit_joint_rank)
            self.assertEqual(cut.predicted_joint_rank, cut.explicit_joint_rank)

    def test_implicit_product_refuses_large_materialization(self) -> None:
        witness = ImplicitProxyKroneckerUnfolding(
            event_matrix=((1, 0), (0, 1)), circuit_dimension=128
        )
        self.assertEqual(witness.exact_rank, 256)
        with self.assertRaises(ValueError):
            witness.materialize(max_entries=1_000)

    def test_exhaustive_search_counts_every_permutation(self) -> None:
        instance = synthetic_instance("aligned", n=6)
        tables = build_structural_tables(instance.event, instance.graph)
        result = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            tables=tables,
        )
        self.assertEqual(result.permutations_evaluated, factorial_permutation_count(6))
        self.assertGreater(result.optimal_order_count, 0)
        self.assertEqual(result.best_joint_J, 3.0)

    def test_search_guard_at_ten_variables(self) -> None:
        event = BooleanEvent.from_support(["0" * 11], n=11)
        graph = InteractionGraph.from_edges(11, [])
        with self.assertRaisesRegex(ValueError, "guarded"):
            exhaustive_permutation_search(event, graph, 0)

    def test_aligned_family_has_a_common_optimal_order(self) -> None:
        instance = synthetic_instance("aligned", n=6)
        tables = build_structural_tables(instance.event, instance.graph)
        event_result = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="event",
            tables=tables,
        )
        circuit_result = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="circuit",
            tables=tables,
        )
        joint_result = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="joint",
            tables=tables,
        )
        natural = instance.event_favoured_order
        profile = order_profile(
            instance.event,
            instance.graph,
            instance.depth,
            natural,
            tables=tables,
        )
        self.assertEqual(profile.max_event_rank, event_result.best_score)
        self.assertEqual(profile.max_crossing_edges, circuit_result.best_score)
        self.assertEqual(profile.max_joint_rank_product, joint_result.best_score)

    def test_anti_aligned_family_exposes_one_sided_failure(self) -> None:
        instance = synthetic_instance("anti_aligned", n=6)
        tables = build_structural_tables(instance.event, instance.graph)
        event_order = order_profile(
            instance.event,
            instance.graph,
            instance.depth,
            instance.event_favoured_order,
            tables=tables,
        )
        circuit_order = order_profile(
            instance.event,
            instance.graph,
            instance.depth,
            instance.circuit_favoured_order,
            tables=tables,
        )
        joint = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="joint",
            tables=tables,
        )
        self.assertEqual(event_order.max_event_rank, 2)
        self.assertEqual(circuit_order.max_crossing_edges, 1)
        self.assertEqual(circuit_order.max_event_rank, 8)
        self.assertLessEqual(joint.best_score, event_order.max_joint_rank_product)
        self.assertLessEqual(joint.best_score, circuit_order.max_joint_rank_product)

    def test_event_easy_family_reduces_to_circuit_ordering(self) -> None:
        instance = synthetic_instance("event_easy", n=6)
        tables = build_structural_tables(instance.event, instance.graph)
        self.assertTrue(all(rank == 1 for rank in tables.event_ranks))
        joint = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="joint",
            tables=tables,
        )
        circuit = exhaustive_permutation_search(
            instance.event,
            instance.graph,
            instance.depth,
            objective="circuit",
            tables=tables,
        )
        self.assertEqual(joint.best_joint_J, 2.0 * instance.depth * circuit.best_score)

    def test_circuit_hard_clique_is_order_invariant(self) -> None:
        instance = synthetic_instance("circuit_hard", n=6)
        first = order_profile(
            instance.event, instance.graph, instance.depth, tuple(range(6))
        )
        second = order_profile(
            instance.event, instance.graph, instance.depth, (0, 2, 4, 1, 3, 5)
        )
        self.assertEqual(first.max_crossing_edges, 9)
        self.assertEqual(second.max_crossing_edges, 9)


if __name__ == "__main__":
    unittest.main()
