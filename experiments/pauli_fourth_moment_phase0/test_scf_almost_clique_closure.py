from fractions import Fraction as F
import json
import unittest
from verify_almost_clique_counterexample import DATA, verify, verify_local, verify_family_sample
from verify_almost_clique_closure_audit import enumerate_independent, verify_audit
from verify_scf_generalization import graph_edges


class AlmostCliqueClosureTests(unittest.TestCase):
    def certificate(self):
        return json.loads((DATA/'almost_clique_closure_counterexample.json').read_text())

    def test_exact_quantum_and_local_proofs(self):
        result = verify(self.certificate())
        self.assertEqual(F(result['exact_gap']),F(556,15625))
        self.assertEqual(result['local_all_weight_proofs']['left']['active_systems_checked'],3432)

    def test_missing_local_rank_facet_rejected(self):
        row = self.certificate()
        certificate = row['local_certificates']['left']
        certificate['facets'] = [f for f in certificate['facets'] if f['kind'] != 'SCF_rank']
        _,edges = graph_edges(row['graph6'])
        with self.assertRaises(AssertionError):
            verify_local(certificate,edges,row['boundary']['left'])

    def test_corrupt_physical_state_rejected(self):
        row = self.certificate()
        row['integer_state_real'][0] += 1
        with self.assertRaises(AssertionError):
            verify(row)

    def test_corrupt_separator_rejected(self):
        row = self.certificate()
        row['boundary']['pair'] = [0,6]
        with self.assertRaises(AssertionError):
            verify(row)

    def test_structural_controls(self):
        self.assertEqual(len(enumerate_independent('Cl')),2)
        self.assertEqual(enumerate_independent('C~'),[])

    def test_independent_benchmark_screen(self):
        result = verify_audit()
        self.assertEqual(result['totals']['8']['with_separator'],9)
        self.assertEqual(result['totals']['9']['decompositions'],5314)

    def test_positive_weight_infinite_family_samples(self):
        certificate = self.certificate()
        for copies in (2,3,4,5):
            result = verify_family_sample(certificate,copies)
            self.assertEqual(result['vertices'],7+copies)
            self.assertEqual(F(result['exact_gap']),F(556,15625))


if __name__ == '__main__':
    unittest.main()
