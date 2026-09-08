"""C007 exact endpoint, homogeneous-row refinement and negative controls."""
import copy
from fractions import Fraction as F
import json
import unittest
from verify_scf_core_refinement import DATA, lifted_description, refine_transport, verify
from verify_scf_uniform_facet_gate import verify as verify_gate, verify_mir, weight_automorphism_exists
from verify_scf_family_facet_closure import cube_clip, verify_polytope
from verify_scf_generalization import graph_edges


class CoreRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = json.loads((DATA/'scf_core_refinement.json').read_text())
        cls.gate = json.loads((DATA/'scf_uniform_facet_gate.json').read_text())

    def test_exact_lifted_core_and_lower_endpoint(self):
        result = verify(self.core)
        self.assertEqual((result['core_vertices'], result['lifted_facets']), (22, 24))
        self.assertEqual(result['exact_lower_z_facets'], 3)

    def test_all_frozen_sizes_independently_complete(self):
        result = verify_gate(self.gate)
        self.assertTrue(result['all_audited_sizes_all_weight_proved'])
        self.assertEqual([r['facets'] for r in result['records']], [23, 27, 31, 35])

    def test_lifted_description_matches_all_four_hulls(self):
        base = self.gate['records'][0]['facets_b_plus_ax']
        for record in self.gate['records']:
            self.assertEqual(lifted_description(record['m'], base), record['facets_b_plus_ax'])

    def test_omitted_lower_facet_fails_geometrically(self):
        report = copy.deepcopy(self.core)
        report['facets_b_plus_ax'].remove(report['lower_z_facets'][-1])
        with self.assertRaisesRegex(AssertionError, 'incomplete lifted core polytope'):
            verify(report)

    def test_corrupted_endpoint_rejected(self):
        report = copy.deepcopy(self.core)
        report['lower_z_facets'][-1][0] += 1
        with self.assertRaises(AssertionError): verify(report)

    def test_corrupted_event_vertex_rejected(self):
        report = copy.deepcopy(self.core)
        report['points'][0][-1] = 1
        with self.assertRaises(AssertionError): verify(report)

    def test_unrestricted_claim_rejected(self):
        report = copy.deepcopy(self.core)
        report['unrestricted_SCF_theorem'] = True
        with self.assertRaises(AssertionError): verify(report)

    def test_legacy_default_dimension_cap_preserved(self):
        with self.assertRaises(AssertionError): cube_clip(11, [])
        # C012 explicitly registers opt-in dimension 15, never the default.
        with self.assertRaises(AssertionError): cube_clip(16, [], max_dimension=16)

    def test_omitted_order12_facet_is_geometrically_detected(self):
        report = copy.deepcopy(self.gate['records'][2])
        del report['facets_b_plus_ax'][-1]
        with self.assertRaisesRegex(AssertionError, 'polyhedral incompleteness'):
            verify_polytope(report, max_dimension=14)

    def test_zero_mass_transport(self):
        self.assertIsNotNone(refine_transport([0, 0], [0, 0], 0))
        self.assertIsNotNone(refine_transport([0, 0], [F(1, 2), 0], 0))

    def test_boundary_and_private_transport(self):
        self.assertIsNotNone(refine_transport([F(1, 2), 0], [F(1, 2), 0], 0))
        self.assertIsNotNone(refine_transport([F(1, 4), F(1, 4), 0], [F(1, 4), F(1, 4), 0], F(1, 2)))
        self.assertIsNotNone(refine_transport([0, F(1, 2)], [0, F(1, 2)], F(1, 2)))

    def test_incompatible_diagonal_transport(self):
        self.assertIsNone(refine_transport([F(1, 2), 0], [F(1, 2), 0], F(1, 2)))

    def test_MIR_positive_C7_and_corrupt_control(self):
        n = 7
        edges = {(i, i+1) for i in range(n-1)} | {(0, n-1)}
        bits = [int((i, j) in edges) for j in range(1, n) for i in range(j)]
        bits += [0]*((-len(bits)) % 6)
        code = chr(n+63)+''.join(chr(63+sum(b << (5-k) for k, b in enumerate(bits[i:i+6])))
                                 for i in range(0, len(bits), 6))
        record = {'graph6': code, 'classical_MIR_identification': {
            'quantum_rounding_claim': False, 'matching_certificates': 1,
            'first_certificate': {'cliques': list(map(list, sorted(edges))), 'p': 7, 'q': 2, 'r': 1,
                                  'multiplicities': [2]*7, 'raw_coefficients': [1]*7,
                                  'raw_rhs': 3, 'primitive_divisor': 1}}}
        self.assertEqual(verify_mir(record, [1]*7)['status'], 'exact_classical_MIR_certificate')
        record['classical_MIR_identification']['first_certificate']['raw_rhs'] = 4
        with self.assertRaises(AssertionError): verify_mir(record, [1]*7)

    def test_independent_weight_orbit_control(self):
        n, edges = graph_edges(self.gate['records'][0]['graph6'])
        w = [1]*5+[2]*3
        self.assertTrue(weight_automorphism_exists(n, edges, w, w))
        self.assertFalse(weight_automorphism_exists(n, edges, w, [1]*8))


if __name__ == '__main__': unittest.main()
