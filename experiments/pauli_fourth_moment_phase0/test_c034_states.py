import copy
import json
import unittest
from verify_c034_states import DATA,verify


class StateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((DATA/'c034_gear_falsification.json').read_text())
    def test_valid(self):self.assertEqual(verify(self.report)['states_checked'],31)
    def test_corrupt_state(self):
        bad=copy.deepcopy(self.report);bad['records'][0]['best']['state'][0][0]+=1
        with self.assertRaises(AssertionError):verify(bad)
    def test_corrupt_weight(self):
        bad=copy.deepcopy(self.report);bad['records'][0]['weights'][0]+=1
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
