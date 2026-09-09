import copy
import json
import unittest
import numpy as np
from fractions import Fraction
from verify_c031_exact_six import DATA,check
from run_c031_dixon import factor,solve_factored
from run_c030_modular_recovery import reconstruct


class ExactSix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cert=json.loads((DATA/'c031_candidate.json').read_text())
    def test_valid(self):
        self.assertEqual(check(self.cert)['fixed_representation_quantum_maximum'],6)
    def test_negative_coordinate(self):
        bad=copy.deepcopy(self.cert);bad['dual_numerators'][0]=-1
        with self.assertRaises(AssertionError):check(bad)
    def test_wrong_denominator(self):
        bad=copy.deepcopy(self.cert);bad['dual_denominator']*=2
        with self.assertRaises(AssertionError):check(bad)
    def test_missing_symmetric_support(self):
        bad=copy.deepcopy(self.cert);bad['symmetric_support_required']=False
        with self.assertRaises(AssertionError):check(bad)
    def test_wrong_source(self):
        bad=copy.deepcopy(self.cert);bad['source_sha256']='0'*64
        with self.assertRaises(AssertionError):check(bad)
    def test_factor_reuse(self):
        a=np.array([[0,2,1],[1,0,3],[2,1,0]],dtype=np.int64)
        upper,steps=factor(a,101)
        for x in ([1,2,3],[7,0,4]):
            x=np.array(x,dtype=np.int64)
            self.assertTrue(np.array_equal(solve_factored(upper,steps,a@x,101),x))


if __name__=='__main__':unittest.main()
