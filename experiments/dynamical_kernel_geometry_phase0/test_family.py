from __future__ import annotations

import unittest

from .run_family import HardBlockadeSystem, leaf_reduction, layout_is_exact, unit_disk_positions, windmill_leaf
from .run_constant_deficit import constant_deficit_graph


class FamilyTests(unittest.TestCase):
    def test_endpoint_bijection_counts(self):
        for k in range(1, 6):
            graph = windmill_leaf(k)
            reduced = leaf_reduction(graph, 0).graph
            original_system = HardBlockadeSystem(graph)
            reduced_system = HardBlockadeSystem(reduced)
            self.assertEqual(original_system.alpha, reduced_system.alpha + 1)
            self.assertEqual(len(original_system.optimum_masks), 2**k)
            self.assertEqual(len(reduced_system.optimum_masks), 2**k)

    def test_unit_disk_layouts(self):
        for k in range(1, 5):
            self.assertTrue(layout_is_exact(windmill_leaf(k), unit_disk_positions(k)))

    def test_constant_deficit_family(self):
        for k in range(1, 5):
            graph = constant_deficit_graph(k)
            reduced = leaf_reduction(graph, 0).graph
            original_system = HardBlockadeSystem(graph)
            reduced_system = HardBlockadeSystem(reduced)
            self.assertEqual(original_system.alpha, k + 2)
            self.assertEqual(reduced_system.alpha + 1, original_system.alpha)
            self.assertEqual(len(original_system.optimum_masks), 2**k)
            self.assertEqual(len(reduced_system.optimum_masks), 2**k)


if __name__ == "__main__":
    unittest.main()
