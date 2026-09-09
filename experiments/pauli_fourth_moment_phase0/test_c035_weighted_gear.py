import copy
import json
import unittest
from verify_c035_weighted_gear import DATA, verify


class WeightedGearAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'c035_weighted_gear.json').read_text())

    def test_valid(self):
        result=verify(self.report)
        self.assertEqual(result['states_checked'],960)
        self.assertEqual(result['violations'],0)

    def corrupt(self, modify):
        bad=copy.deepcopy(self.report)
        modify(bad['records'][0])
        with self.assertRaises(AssertionError):
            verify(bad)

    def test_corrupt_state(self):
        self.corrupt(lambda r:r['runs'][0]['state'][0].__setitem__(0,10))

    def test_corrupt_seed_weight(self):
        self.corrupt(lambda r:r['seed_weights'].__setitem__(r['seed_edge'][0],2))

    def test_corrupt_residual(self):
        self.corrupt(lambda r:r['runs'][0].__setitem__('stationarity_residual',1))

    def test_corrupt_bound(self):
        self.corrupt(lambda r:r.__setitem__('bound',r['bound']+1))


if __name__=='__main__':
    unittest.main()
