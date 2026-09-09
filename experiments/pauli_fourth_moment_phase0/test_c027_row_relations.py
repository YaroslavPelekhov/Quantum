import copy
import json
import unittest
from verify_c027_row_relations import DATA,verify


class ExactRelations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert=json.loads((DATA/'c027_row_relations_fraction.json').read_text())
    def test_valid(self):
        self.assertTrue(verify(self.cert)['equivalence_proved'])
    def test_corrupted_coefficient(self):
        bad=copy.deepcopy(self.cert);bad['numerators'][0][0]+=1
        with self.assertRaises(AssertionError):verify(bad)
    def test_missing_row(self):
        bad=copy.deepcopy(self.cert);bad['deleted_rows'].pop();bad['numerators'].pop()
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
