from __future__ import annotations

import itertools
import sys
import unittest
from pathlib import Path

import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from representation_screen import (  # noqa: E402
    build_qaoa_density_network,
    compile_local_mis_cardinality,
    compile_rank_minimal_support_tt,
    enumerate_independent_set_support,
    evaluate_local_mis_cardinality,
    evaluate_support_tt,
    optimize_contraction_path,
    run_representation_screen,
)


class RepresentationScreenTests(unittest.TestCase):
    def test_support_enumeration_defaults_to_maximum_independent_sets(self) -> None:
        target, support = enumerate_independent_set_support(nx.cycle_graph(4))
        self.assertEqual(target, 2)
        self.assertEqual(set(support), {"0101", "1010"})

    def test_support_tt_has_exact_unfolding_ranks_in_reversed_order(self) -> None:
        support = ("0000", "0011", "1010", "1100")
        order = (3, 2, 1, 0)
        encoding = compile_rank_minimal_support_tt(support, order)
        dense = np.zeros((2,) * 4)
        for value in support:
            dense[tuple(int(value[qubit]) for qubit in order)] = 1.0
        expected = [1]
        for cut in range(1, 4):
            expected.append(
                int(np.linalg.matrix_rank(dense.reshape(2**cut, 2 ** (4 - cut))))
            )
        expected.append(1)
        self.assertEqual(list(encoding.ranks), expected)

    def test_event_encodings_are_equivalent_for_every_assignment(self) -> None:
        graph = nx.cycle_graph(5)
        target, support = enumerate_independent_set_support(graph, 2)
        support_set = set(support)
        for order in ((0, 1, 2, 3, 4), (4, 2, 0, 3, 1)):
            tt = compile_rank_minimal_support_tt(support, order)
            local = compile_local_mis_cardinality(graph, target, order)
            for bits in itertools.product((0, 1), repeat=5):
                bitstring = "".join(map(str, bits))
                expected = float(bitstring in support_set)
                self.assertAlmostEqual(evaluate_support_tt(tt, bitstring), expected)
                self.assertAlmostEqual(
                    evaluate_local_mis_cardinality(local, bitstring), expected
                )

    def test_both_qaoa_networks_are_closed_and_have_complete_paths(self) -> None:
        graph = nx.path_graph(4)
        target, support = enumerate_independent_set_support(graph)
        encodings = (
            compile_rank_minimal_support_tt(support),
            compile_local_mis_cardinality(graph, target),
        )
        for encoding in encodings:
            network = build_qaoa_density_network(graph, 1, encoding)
            network.validate_closed()
            result = optimize_contraction_path(
                network, backend="shape-greedy", trials=3, seed=7
            )
            self.assertEqual(len(result.path), len(network.tensors) - 1)
            self.assertGreater(result.estimated_flops, 0)
            self.assertGreater(result.peak_elements, 0)

    def test_screen_reports_shape_only_costs_for_both_representations(self) -> None:
        graph = nx.path_graph(3)
        report = run_representation_screen(
            graph,
            depth=0,
            orders=(("natural", (0, 1, 2)), ("reverse", (2, 1, 0))),
            backend="shape-greedy",
            trials=3,
            seed=11,
        )
        self.assertTrue(report["optimizer"]["shape_only"])
        self.assertFalse(report["optimizer"]["performs_contraction"])
        self.assertEqual(len(report["rows"]), 4)
        self.assertEqual(
            {row["representation"] for row in report["rows"]},
            {"rank_minimal_support_mpo", "local_mis_plus_cardinality"},
        )
        self.assertTrue(all(row["path"]["path_length"] > 0 for row in report["rows"]))
        self.assertTrue(all(audit["passed"] for audit in report["semantic_audits"]))


if __name__ == "__main__":
    unittest.main()
