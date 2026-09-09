from fractions import Fraction
import unittest
from run_c030_modular_recovery import modular_solve,reconstruct


class ModularCorrection(unittest.TestCase):
    def test_fractional_solution(self):
        values=modular_solve([[2,1],[1,3]],[1,0],101)
        self.assertEqual([reconstruct(v,101) for v in values],[Fraction(3,5),Fraction(-1,5)])
    def test_pivot_swap(self):
        self.assertEqual(modular_solve([[0,1],[1,0]],[2,3],101),[3,2])
    def test_singular_prime(self):
        self.assertIsNone(modular_solve([[1,2],[2,4]],[1,2],101))
    def test_zero(self):
        self.assertEqual(reconstruct(0,101),0)


if __name__=='__main__':unittest.main()
