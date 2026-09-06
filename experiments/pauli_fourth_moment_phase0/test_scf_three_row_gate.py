import copy
import itertools as it
import json
import unittest
from verify_scf_three_row_gate import (DATA, edges_from_cells, verify_row, verify_census,
                                       verify_target, gf2_rank, elementary_reductions)


class ThreeRowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.census = json.loads((DATA/'scf_three_row_gate.json').read_text())
        cls.target = json.loads((DATA/'scf_three_row_target.json').read_text())

    def test_entire_frozen_structural_census(self):
        self.assertEqual(verify_census(self.census)['graphs'], 4096)

    def test_exact_target_hull_and_obstructions(self):
        r = verify_target(self.target)
        self.assertEqual((r['STAB_vertices'], r['facets'], r['GF2_adjacency_rank']), (46, 36, 6))
        self.assertFalse(any(r['elementary_reductions'].values()))

    def test_empty_claw_and_C005_controls(self):
        cases = [([], 0, True), ([(0, 1), (1, 2), (2, 3)], 3, False),
                 ([(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2), (1, 3)], 2, True)]
        for cells, matching, scf in cases:
            mask = sum(1 << (4*r+c) for r, c in cells)
            self.assertEqual(verify_row(self.census['records'][mask]), matching)
            self.assertEqual(self.census['records'][mask]['SCF'], scf)

    def test_three_row_selectors_are_line_graphs_on_all_grid_patterns(self):
        for mask in range(4096):
            cells = [(r, c) for r in range(3) for c in range(4) if mask >> (4*r+c) & 1]
            root = [{r, 3+c} for r, c in cells]+[{1, 2}, {0, 2}, {0, 1}]
            line_edges = {(i, j) for i, j in it.combinations(range(len(root)), 2) if root[i] & root[j]}
            self.assertEqual(edges_from_cells(cells, three_rows=True), (len(root), line_edges))

    def test_bad_graph_and_matching_rejected(self):
        row = copy.deepcopy(self.census['records'][2114])
        row['graph6'] = self.census['records'][0]['graph6']
        with self.assertRaises(AssertionError): verify_row(row)
        row = copy.deepcopy(self.census['records'][2114])
        row['matching'][0] = row['matching'][1]
        with self.assertRaises(AssertionError): verify_row(row)

    def test_bad_cover_and_claw_rejected(self):
        row = copy.deepcopy(self.census['records'][2114])
        row['minimum_cover'] = []
        with self.assertRaises(AssertionError): verify_row(row)
        row = copy.deepcopy(self.census['records'][2114])
        row['claw'] = None
        with self.assertRaises(AssertionError): verify_row(row)

    def test_omitted_full_target_facet_fails_geometrically(self):
        report = copy.deepcopy(self.target)
        report['target']['facets_b_plus_ax'].remove([3]+[-1]*9+[-2]*3)
        with self.assertRaisesRegex(AssertionError, 'polyhedral incompleteness'):
            verify_target(report)

    def test_unsupported_quantum_claim_rejected(self):
        report = copy.deepcopy(self.target)
        report['all_weight_quantum_theorem'] = True
        with self.assertRaises(AssertionError): verify_target(report)

    def test_GF2_rank_controls(self):
        self.assertEqual(gf2_rank(3, set()), 0)
        self.assertEqual(gf2_rank(3, {(0, 1), (0, 2), (1, 2)}), 2)
        self.assertEqual(gf2_rank(4, {(0, 1), (2, 3)}), 4)
        path = elementary_reductions(3, {(0, 1), (1, 2)})
        self.assertEqual(path['copy_pairs'], [[0, 2]])
        self.assertEqual(path['clique_separators'], [[1]])
        self.assertEqual(elementary_reductions(3, {(0, 1), (0, 2), (1, 2)})['split_pairs'],
                         [[0, 1], [0, 2], [1, 2]])


if __name__ == '__main__': unittest.main()
