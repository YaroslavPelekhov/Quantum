import copy
import unittest
from run_c032_prior_structure import audit,verify_traces


class Structure(unittest.TestCase):
    def test_prime_path_four(self):
        g=[{1},{0,2},{1,3},{2}];result=audit(g);verify_traces(g,result)
        self.assertTrue(result['modular_prime'])
    def test_cycle_four_twins(self):
        g=[{1,3},{0,2},{1,3},{0,2}];result=audit(g);verify_traces(g,result)
        self.assertFalse(result['modular_prime']);self.assertEqual(len(result['twins']),2)
    def test_invalid_addition(self):
        g=[{1,3},{0,2},{1,3},{0,2}];result=audit(g)
        # Pair (0,2) is a module: adding 1 cannot be forced.
        result['pair_closure_traces'][1].append(1)
        with self.assertRaises(AssertionError):verify_traces(g,result)


if __name__=='__main__':unittest.main()
