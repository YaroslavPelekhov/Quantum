"""C010 endpoint, finite completeness and uniform-reduction controls."""
import copy
from collections import Counter
from fractions import Fraction as F
import json
import unittest
from verify_scf_d_closure import DATA, verify, cover_route
from verify_scf_family_facet_closure import cube_clip
from verify_scf_core_refinement import refine_transport


class DClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = json.loads((DATA/'scf_d_core_c010.json').read_text())
        cls.family = json.loads((DATA/'scf_d_family_c010.json').read_text())

    def test_exact_acceptance(self):
        self.assertEqual(len(verify(self.core, self.family)['records']), 4)

    def test_missing_lower_facet_geometrically(self):
        facets = copy.deepcopy(self.core['facets_b_plus_ax'])
        facets.remove(self.core['lower_z_facets'][-1])
        found, _ = cube_clip(9, facets)
        self.assertNotEqual(found, set(map(tuple, self.core['points'])))

    def test_wrong_joint_event(self):
        core = copy.deepcopy(self.core)
        core['points'][0][-1] = 1
        with self.assertRaises(AssertionError): verify(core, self.family)

    def test_wrong_endpoint(self):
        core = copy.deepcopy(self.core)
        core['lower_z_facets'][-1][0] = 3
        with self.assertRaises(AssertionError): verify(core, self.family)

    def test_bad_scope(self):
        core = copy.deepcopy(self.core)
        core['A_star_confirmed'] = True
        with self.assertRaises(AssertionError): verify(core, self.family)

    def test_transport_without_private_mass(self):
        # Existing exact Hall implementation: final private labels have mass zero.
        self.assertIsNotNone(refine_transport([F(1, 4), F(1, 4), 0], [F(1, 4), F(1, 4), 0], F(1, 2)))
        self.assertIsNone(refine_transport([F(1, 2), 0], [F(1, 2), 0], F(1, 2)))
        self.assertIsNotNone(refine_transport([0], [0], 0))

    def test_existing_C008_cover_witnesses(self):
        source = json.loads((DATA/'scf_three_row_gate.json').read_text())
        counts = Counter()
        for row in source['records']:
            if row['SCF']:
                mask = row['cell_mask']
                cells = [(r, c) for r in range(3) for c in range(4) if mask >> (4*r+c) & 1]
                counts[cover_route(cells)] += 1
        self.assertEqual(sum(counts.values()), 2120)

    def test_claw_control_rejected(self):
        with self.assertRaises(AssertionError): cover_route([(0, 1), (1, 2), (2, 3)])


if __name__ == '__main__':
    unittest.main()
