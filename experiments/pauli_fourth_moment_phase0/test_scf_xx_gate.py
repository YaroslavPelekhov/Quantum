"""C011 published graph and exact certificate corruption controls."""
import copy
import json
import unittest
from verify_scf_xx_gate import verify, DATA


class XXGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((DATA/'scf_xx_gate_c011.json').read_text())

    def test_complete_independent_acceptance(self):
        result = verify(self.report)
        self.assertEqual(result['records'][0]['STAB_vertices'],85)
        self.assertTrue(result['dependency_C009_rechecked'])

    def rejected(self, change):
        r = copy.deepcopy(self.report)
        change(r)
        with self.assertRaises(AssertionError): verify(r,full=False)

    def test_wrong_graph(self):
        self.rejected(lambda r:r['records'][0].update(graph6='K{S{aSfF~Fln'))

    def test_wrong_original_labels(self):
        self.rejected(lambda r:r['records'][0]['original_labels'].reverse())

    def test_wrong_embedding(self):
        def change(r):
            route = next(x for x in r['records'][0]['routes'] if x['route']=='C009_induced')
            route['C009_mapping']['0']=1
        self.rejected(change)

    def test_wrong_facet(self):
        self.rejected(lambda r:r['records'][0]['facets_b_plus_ax'][-1].__setitem__(0,4))

    def test_overclaim(self):
        for key in ('quantum_all_weight_theorem','unrestricted_SCF_theorem','A_star_confirmed'):
            self.rejected(lambda r,key=key:r.update({key:True}))


if __name__=='__main__': unittest.main()
