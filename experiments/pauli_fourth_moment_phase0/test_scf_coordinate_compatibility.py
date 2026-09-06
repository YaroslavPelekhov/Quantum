from fractions import Fraction as F
import json
import unittest
from verify_scf_coordinate_compatibility import DATA, verify_all, verify_witness


class CoordinateCompatibilityTests(unittest.TestCase):
    def canonical(self):
        rows = json.loads((DATA/'scf_coordinate_compatibility.json').read_text())['records']
        return next(r for r in rows if r['label'] == 'order9_residual_33')

    def test_all_exact_obstructions(self):
        self.assertEqual(verify_all()['exact_obstructions'],8)

    def test_canonical_joint_contradiction(self):
        row = self.canonical()
        self.assertEqual(verify_witness(row),F(1,8))
        self.assertEqual(row['joint_pair_sum_ranges']['left']['upper'],'1/4')
        self.assertEqual(row['joint_pair_sum_ranges']['right']['lower'],'1/2')

    def test_corrupt_coordinate_marginal_rejected(self):
        row = self.canonical()
        row['pairwise_decompositions'][0]['left'][0]['probability'] = '1/3'
        with self.assertRaises(AssertionError):
            verify_witness(row)

    def test_corrupt_joint_dual_rejected(self):
        row = self.canonical()
        row['joint_pair_sum_ranges']['left']['upper_dual'][0] = '100'
        with self.assertRaises(AssertionError):
            verify_witness(row)


if __name__ == '__main__':
    unittest.main()
