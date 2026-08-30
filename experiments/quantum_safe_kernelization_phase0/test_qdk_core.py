from __future__ import annotations

import unittest

import networkx as nx

from .qdk_core import HardBlockadeSystem, gap_distortion, leaf_reduction, lifted_optimum_count, schedule


class QDKCoreTests(unittest.TestCase):
    def test_independent_set_basis_path3(self):
        system = HardBlockadeSystem(nx.path_graph(3))
        self.assertEqual(set(system.masks), {0, 1, 2, 4, 5})
        self.assertEqual(system.alpha, 2)

    def test_leaf_rule_exact(self):
        graph = nx.path_graph(4)
        reduction = leaf_reduction(graph, 0)
        self.assertEqual(HardBlockadeSystem(graph).alpha, HardBlockadeSystem(reduction.graph).alpha + 1)
        lifted, total = lifted_optimum_count(graph, reduction)
        self.assertLessEqual(lifted, total)

    def test_schedule_endpoints(self):
        self.assertEqual(schedule(0.0), (0.0, -2.0))
        self.assertEqual(schedule(1.0), (0.0, 2.0))

    def test_gap_distortion_is_symmetric(self):
        self.assertEqual(gap_distortion(2.0, 0.5), 4.0)
        self.assertEqual(gap_distortion(0.5, 2.0), 4.0)


if __name__ == "__main__":
    unittest.main()
