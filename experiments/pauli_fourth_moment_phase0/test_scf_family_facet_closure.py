"""C006 exact completeness and adversarial regression controls (stdlib)."""
import copy
from fractions import Fraction as F
import itertools
import json
import unittest
from verify_scf_generalization import graph_edges
from verify_scf_family_facet_closure import (
    DATA, componentwise_scf, cube_clip, value, verify, verify_polytope)


class FacetClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((DATA/'scf_family_facet_closure.json').read_text())

    def test_complete_target_and_proof_routes(self):
        result = verify(self.report)
        self.assertEqual((result['vertices'], result['facets']), (34, 27))
        self.assertEqual(result['routes'], {'nonnegativity': 10, 'SCF_rank': 14,
                                           'SCF_order9_all_weights': 2, 'C005_rectangular_Gram': 1})

    def test_path_and_odd_cycle_controls(self):
        for record, counts in zip(self.report['controls'], ((8, 7), (11, 11))):
            result = verify_polytope(record)
            self.assertEqual((result['vertices'], result['facets']), counts)

    def test_missing_facet_is_geometrically_detected(self):
        target = copy.deepcopy(self.report['target'])
        del target['facets_b_plus_ax'][self.report['missing_facet_control']['removed_facet_index']]
        with self.assertRaisesRegex(AssertionError, 'polyhedral incompleteness'):
            verify_polytope(target)

    def test_exact_missing_facet_witness(self):
        target = self.report['target']
        omitted = self.report['missing_facet_control']['removed_facet_index']
        self.assertEqual(len(self.report['missing_facet_control']['extra_vertices']), 3)
        for raw in self.report['missing_facet_control']['extra_vertices']:
            point = tuple(map(F, raw))
            self.assertEqual(value(target['facets_b_plus_ax'][omitted], point), F(-1, 4))
            self.assertTrue(all(value(row, point) >= 0
                                for i, row in enumerate(target['facets_b_plus_ax']) if i != omitted))

    def test_corrupted_coefficient_rejected(self):
        target = copy.deepcopy(self.report['target'])
        target['facets_b_plus_ax'][-1][1] -= 1
        with self.assertRaises(AssertionError):
            verify_polytope(target)

    def test_corrupted_graph_rejected(self):
        report = copy.deepcopy(self.report)
        report['target']['graph6'] = report['controls'][1]['graph6']
        with self.assertRaises(AssertionError):
            verify(report)

    def test_duplicate_row_rejected(self):
        target = copy.deepcopy(self.report['target'])
        target['facets_b_plus_ax'].append(target['facets_b_plus_ax'][-1])
        with self.assertRaisesRegex(AssertionError, 'duplicate facet'):
            verify_polytope(target)

    def test_wrong_quantum_route_rejected(self):
        report = copy.deepcopy(self.report)
        row = report['target']['proof_routes'][-1]
        self.assertEqual(row['route'], 'C005_rectangular_Gram')
        row['route'] = 'SCF_rank'
        with self.assertRaises(AssertionError):
            verify(report)

    def test_simplicial_clique_need_not_be_maximal(self):
        target = self.report['target']
        n, edges = graph_edges(target['graph6'])
        supports = [r['support'] for r in target['proof_routes'] if r['route'] == 'SCF_order9_all_weights']
        self.assertEqual(len(supports), 2)
        def clique(nodes):
            return all(tuple(sorted(pair)) in edges for pair in itertools.combinations(nodes, 2))
        for support in supports:
            self.assertTrue(componentwise_scf(n, edges, support))
            simplicial = []
            for mask in range(1, 1 << len(support)):
                nodes = {v for i, v in enumerate(support) if mask >> i & 1}
                if clique(nodes) and all(clique({u for u in support if u not in nodes
                                                 and tuple(sorted((u, v))) in edges}) for v in nodes):
                    simplicial.append(nodes)
            self.assertTrue(simplicial)
            # Every simplicial clique here is strictly extendible as a
            # clique; searching only maximal cliques produces a false NO.
            self.assertTrue(all(any(clique(nodes | {u}) for u in set(support)-nodes)
                                for nodes in simplicial))

    def test_clip_keeps_boundary_vertices_and_handles_rationals(self):
        points, _ = cube_clip(2, [[1, -1, -1], [1, -2, -1]])
        self.assertEqual(points, {(F(0), F(0)), (F(0), F(1)), (F(1, 2), F(0))})


if __name__ == '__main__':
    unittest.main()
