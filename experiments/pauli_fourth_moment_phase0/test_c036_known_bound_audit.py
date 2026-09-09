import copy
import json
import unittest
from verify_c036_known_bound_audit import DATA,verify


class ExactKnownBoundAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'c036_known_bound_audit.json').read_text())

    def test_valid(self):
        result=verify(self.report)
        self.assertEqual(result['clique_explained'],40)
        self.assertEqual(len(result['frontier']),20)

    def test_corrupt_primal(self):
        bad=copy.deepcopy(self.report)
        bad['records'][0]['clique']['primal'][0]='100'
        with self.assertRaises(AssertionError):verify(bad)

    def test_corrupt_dual(self):
        bad=copy.deepcopy(self.report)
        bad['records'][0]['clique']['dual'][0]['coefficient']='-1'
        with self.assertRaises(AssertionError):verify(bad)

    def test_corrupt_row(self):
        bad=copy.deepcopy(self.report)
        bad['records'][0]['clique']['dual'][0]['bound']=0
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
