import unittest
from pathlib import Path

import numpy as np

from qaoa_mis import (
    distribution_metrics,
    enumerate_exact_space,
    induced_subgraph,
    load_dimacs_graph,
    repair_mask,
    statevector_probabilities,
)
from feasible_mixer import FeasibleMixerSimulator


ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "QOBLIB" / "07-independentset" / "instances" / "mammalia-kangaroo-interactions.gph"


class QAOAMISTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = load_dimacs_graph(GRAPH)
        cls.exact = enumerate_exact_space(cls.graph)

    def test_qoblib_instance_and_exact_optimum(self):
        self.assertEqual((self.graph.n, len(self.graph.edges)), (17, 91))
        self.assertEqual(self.exact.optimum, 4)

    def test_known_qoblib_solution(self):
        mask = sum(1 << (vertex - 1) for vertex in [2, 6, 7, 8])
        self.assertTrue(bool(self.exact.feasible[mask]))
        self.assertEqual(int(self.exact.sizes[mask]), 4)

    def test_repair_always_feasible_on_deterministic_sample(self):
        for mask in range(0, 1 << self.graph.n, 997):
            self.assertTrue(bool(self.exact.feasible[repair_mask(mask, self.graph)]))

    def test_statevector_is_normalized(self):
        probs = statevector_probabilities(self.graph, np.array([2.0, 0.5, 0.7]), p=1)
        self.assertAlmostEqual(float(probs.sum()), 1.0, places=10)
        self.assertGreaterEqual(distribution_metrics(probs, self.exact)["score"], 0.0)

    def test_normalized_cost_and_induced_graph(self):
        subgraph = induced_subgraph(self.graph, range(12), "first12")
        self.assertEqual(subgraph.n, 12)
        self.assertTrue(all(max(edge) < 12 for edge in subgraph.edges))
        probs = statevector_probabilities(
            subgraph, np.array([2.0, 0.5, 0.4, 0.7, 1.1]), p=2, cost_scale="max_coefficient"
        )
        self.assertAlmostEqual(float(probs.sum()), 1.0, places=10)

    def test_feasible_mixer_never_leaves_independent_sets(self):
        simulator = FeasibleMixerSimulator(self.graph, self.exact)
        params = np.array([1.2, 0.3, 0.7, 1.1, 0.9, 1.4])
        probs = simulator.probabilities(params)
        self.assertAlmostEqual(float(probs.sum()), 1.0, places=10)
        self.assertLess(float(probs[~self.exact.feasible].sum()), 1e-12)


if __name__ == "__main__":
    unittest.main()
