import json
import unittest
from verify_scf_separator_coverage import DATA, exhaustive, verify_all, verify_record


class SeparatorCoverageTests(unittest.TestCase):
    def test_full_independent_coverage(self):
        result = verify_all()
        self.assertEqual(result['types_verified'],47)
        self.assertEqual(result['minimum_pair_histogram_types'],{'1':36,'2':8,'3':3})

    def test_corrupt_minimum_rejected(self):
        row = json.loads((DATA/'scf_separator_coverage.json').read_text())['records'][3]
        row['minimum_pair_events'] = 1
        with self.assertRaises(AssertionError):
            verify_record(row)

    def test_corrupt_boundary_witness_rejected(self):
        row = json.loads((DATA/'scf_separator_coverage.json').read_text())['records'][0]
        row['best']['pairs'] = []
        with self.assertRaises(AssertionError):
            verify_record(row)

    def test_controls(self):
        self.assertEqual(exhaustive(4,{(0,1),(1,2),(2,3)})[1][0],0)
        self.assertEqual(exhaustive(4,{(0,1),(1,2),(2,3),(0,3)})[1][0],1)
        self.assertIsNone(exhaustive(4,{(i,j) for i in range(4) for j in range(i+1,4)})[1])


if __name__ == '__main__':
    unittest.main()
