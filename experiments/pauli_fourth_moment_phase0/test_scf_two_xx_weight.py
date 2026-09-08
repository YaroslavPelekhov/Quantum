"""C014 exact target corruption controls."""
import copy
import json
import unittest
from verify_scf_two_xx_weight import verify,DATA


class TwoXXWeightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((DATA/'scf_two_xx_weight_c014.json').read_text())

    def rejected(self,change):
        r=copy.deepcopy(self.report);change(r)
        with self.assertRaises(AssertionError):verify(r)

    def test_exact_face_and_representation(self):
        r=verify(self.report)
        self.assertEqual(r['STAB_vertices'],2167)
        self.assertEqual(r['weights'][0]['rank'],24)
        self.assertEqual(r['weights'][1]['rank'],6)

    def test_wrong_graph(self):self.rejected(lambda r:r.update(graph6='LhEM?rcNLhleuo'))
    def test_wrong_weight(self):self.rejected(lambda r:r['records'][0]['weights'].__setitem__(0,2))
    def test_wrong_bound(self):self.rejected(lambda r:r['records'][0].update(stable_bound=7))
    def test_missing_tight_set(self):self.rejected(lambda r:r['records'][0]['tight_masks'].pop())
    def test_wrong_Pauli(self):self.rejected(lambda r:r['standard_SAUR_labels'].__setitem__(0,[0,0]))
    def test_overclaim(self):self.rejected(lambda r:r.update(quantum_target_proved=True))


if __name__=='__main__':unittest.main()
