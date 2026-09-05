"""Exact checks, regression controls, and deliberately corrupted certificates."""
import copy
import itertools
import json
from pathlib import Path
import unittest
import networkx as nx
from rationalize_scf_dual import verify
from run_scf_gram_completion import transfer_coefficients, gram_proof, check_envelope
from run_scf_atom_spectral_reduction import (
    multiply_words, verify_univariate_factorization,
    verify_heavy_split_hessian_factorization, verify_full_heavy_simplex_exclusion,
    verify_three_heavy_boundary_classification, verify_residual_two_heavy_faces,
    verify_zero_light_boundary_certificates)

DATA = Path(__file__).resolve().parents[2]/'results'/'pauli_fourth_moment_phase0'


class ExactCompletionTests(unittest.TestCase):
    def certificate(self, index):
        return json.loads((DATA/f'scf_exact_dual{index}.json').read_text())

    def test_rational_duals(self):
        for index, dimension in [(24, 42), (25, 40)]:
            with self.subTest(index=index):
                self.assertEqual(verify(self.certificate(index))['positive_rational_LDL_pivots'], dimension)

    def test_corrupt_graph_is_rejected(self):
        cert = self.certificate(24)
        cert['edges'].pop()
        with self.assertRaises(AssertionError):
            verify(cert)

    def test_corrupt_weight_is_rejected(self):
        cert = self.certificate(24)
        cert['weights'][0] = '100'
        with self.assertRaises(AssertionError):
            verify(cert)

    def test_indefinite_gram_is_rejected(self):
        cert = self.certificate(25)
        cert['rational_gram'][0][0] = '-1'
        with self.assertRaises(AssertionError):
            verify(cert)

    def test_wrong_polynomial_identity_is_rejected(self):
        # Preserve positive definiteness but destroy the affine identity.
        cert = self.certificate(24)
        from fractions import Fraction
        cert['rational_gram'][0][0] = str(Fraction(cert['rational_gram'][0][0])+1)
        with self.assertRaises(AssertionError):
            verify(cert)

    def test_two_exact_gram_completions(self):
        records = json.loads((DATA/'scf_order9_facet_reduction.json').read_text())['residual_atoms']
        check_envelope()
        for record in records:
            if record['representative_index'] in (15, 23):
                graph = nx.from_graph6_bytes(record['support_graph6'].encode())
                self.assertEqual(gram_proof(record, transfer_coefficients(graph))['exact_beta'], '3/2')

    def test_oriented_cycle_sign_regression(self):
        graph = nx.from_graph6_bytes(b'HQjVJr\\')
        cycles = [(0, 1, 6, 8), (0, 7, 2, 8), (1, 2, 6, 7)]
        for i, j in itertools.combinations(range(3), 2):
            product = multiply_words(graph, cycles[i], cycles[j])
            target = multiply_words(graph, (), cycles[3-i-j])
            self.assertEqual(product, (target[0], -target[1]))

    def test_preceding_hard_atom_symbolic_checks(self):
        for check in [verify_univariate_factorization,
                      verify_heavy_split_hessian_factorization,
                      verify_full_heavy_simplex_exclusion,
                      verify_three_heavy_boundary_classification,
                      verify_residual_two_heavy_faces,
                      verify_zero_light_boundary_certificates]:
            with self.subTest(check=check.__name__):
                check()

    def test_complete_exact_census(self):
        census = json.loads((DATA/'scf_exact_facet_census.json').read_text())
        self.assertEqual((census['graphs'], census['total_facets'], census['nonrank_occurrences'], census['nonrank_types']),
                         (3598, 56792, 701, 128))
        self.assertTrue(all(r['exact_roundtrip'] for r in census['records']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
