"""C009 exact identities, independent engines and corrupted certificates."""
import copy
import json
import unittest
from run_scf_three_row_gram import calculate, ParityAlgebra
from verify_scf_three_row_gram import verify, DATA
from verify_scf_rectangular_gram_bridge import Algebra


class ThreeRowGramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((DATA/'scf_three_row_gram_c009.json').read_text())

    def test_independent_acceptance(self):
        self.assertTrue(verify(self.report)['target_all_weight_theorem_supported'])

    def test_discovery_reproduction(self):
        self.assertEqual(calculate(), self.report)

    def test_all_word_products(self):
        # Exhaustive support products on a four-generator graph.
        edges = {(0, 1), (1, 2), (2, 3), (0, 3), (1, 3)}
        p, q = ParityAlgebra(4, edges), Algebra(4, edges)
        words = [{(tuple(i for i in range(4) if s >> i & 1), (0,)*4): 1} for s in range(16)]
        for x in words:
            for y in words:
                self.assertEqual(p.mul(x, y), q.mul(x, y))

    def rejected(self, mutate):
        report = copy.deepcopy(self.report)
        mutate(report)
        with self.assertRaises(AssertionError):
            verify(report, hull=False)

    def test_wrong_center_phase(self):
        self.rejected(lambda r: r['central_checks'][0]['expression'][0].update(coefficient=1))

    def test_wrong_transfer(self):
        self.rejected(lambda r: r['transfer_coefficients'][2][0].update(coefficient=999))

    def test_wrong_candidate(self):
        self.rejected(lambda r: r['candidate_coefficients'][1][0].update(coefficient=999))

    def test_missing_odd_check(self):
        self.rejected(lambda r: r.update(odd_zero=[True, False, True]))

    def test_wrong_graph(self):
        self.rejected(lambda r: r.update(graph6='G{Plg{'))

    def test_overclaim(self):
        for key in ('quantum_bound_proved', 'unrestricted_SCF_theorem', 'A_star_confirmed'):
            self.rejected(lambda r, key=key: r.update({key: True}))


if __name__ == '__main__':
    unittest.main()
