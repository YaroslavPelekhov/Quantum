"""Negative controls for C020's exact acceptance logic."""
import copy
import json
import unittest
from c020_exact_certificate import DATA,verify


class ExactPPT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert=json.loads((DATA/'c020_exact_ppt_certificate.json').read_text())

    def test_valid(self):
        self.assertTrue(verify(self.cert)['PPT_route_to_six_excluded'])

    def test_negative_probability(self):
        bad=copy.deepcopy(self.cert);bad['numerators'][0]=-1
        with self.assertRaises(AssertionError):verify(bad)

    def test_wrong_trace(self):
        bad=copy.deepcopy(self.cert);bad['denominator']+=1
        with self.assertRaises(AssertionError):verify(bad)

    def test_non_ppt_bell_state(self):
        bad=copy.deepcopy(self.cert);bad['numerators']=[1]+[0]*16383;bad['denominator']=1
        with self.assertRaises(AssertionError):verify(bad)

    def test_wrong_objective(self):
        bad=copy.deepcopy(self.cert);bad['exact_value']='7'
        with self.assertRaises(AssertionError):verify(bad)

    def test_changed_source(self):
        bad=copy.deepcopy(self.cert);bad['source_sha256']='0'*64
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
