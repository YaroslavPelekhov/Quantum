import copy
import json
import unittest
from c021_exact_dual import DATA,verify


class ExactDual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cert=json.loads((DATA/'c021_exact_dual_certificate.json').read_text())
    def test_valid_bound_is_not_six(self):
        self.assertFalse(verify(self.cert)['exact_bound_six_proved'])
    def test_false_six(self):
        bad=copy.deepcopy(self.cert);bad['exact_upper']='6'
        with self.assertRaises(AssertionError):verify(bad)
    def test_negative_dual(self):
        bad=copy.deepcopy(self.cert);bad['dual_numerators'][0]=-1
        with self.assertRaises(AssertionError):verify(bad)
    def test_missing_support_condition(self):
        bad=copy.deepcopy(self.cert);bad['symmetric_support_required']=False
        with self.assertRaises(AssertionError):verify(bad)
    def test_wrong_source(self):
        bad=copy.deepcopy(self.cert);bad['source_sha256']='0'*64
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
