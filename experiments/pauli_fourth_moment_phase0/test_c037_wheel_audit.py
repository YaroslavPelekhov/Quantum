import copy
import json
import unittest
from verify_c037_wheel_audit import DATA,verify


class WheelAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((DATA/'c037_wheel_audit.json').read_text())
    def test_valid(self):
        result=verify(self.report)
        self.assertEqual(result['explained'],53)
        self.assertEqual(len(result['frontier']),7)
    def test_corrupt_hub_weight(self):
        bad=copy.deepcopy(self.report)
        wheel=next(t for r in bad['records'] for t in r['dual'] if t['kind']=='odd_wheel')
        wheel['weights'][-1]+=1
        with self.assertRaises(AssertionError):verify(bad)
    def test_corrupt_primal(self):
        bad=copy.deepcopy(self.report);bad['records'][0]['primal'][0]='100'
        with self.assertRaises(AssertionError):verify(bad)
    def test_corrupt_target(self):
        bad=copy.deepcopy(self.report);bad['records'][0]['target']+=1
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
