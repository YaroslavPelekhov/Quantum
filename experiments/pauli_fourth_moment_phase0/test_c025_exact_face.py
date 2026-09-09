import copy
import json
import unittest
from verify_c025_exact_face import DATA,verify


class ExactFace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert=json.loads((DATA/'c025_exact_face.json').read_text())
    def test_valid(self):
        self.assertEqual(verify(self.cert)['complete_spaces'],1320)
    def test_missing_space(self):
        bad=copy.deepcopy(self.cert);bad['spaces'].pop();bad['maximal_isotropic_spaces']-=1
        with self.assertRaises(AssertionError):verify(bad)
    def test_wrong_probability(self):
        bad=copy.deepcopy(self.cert);bad['aggregate_lambda_numerators'][0]+=1
        with self.assertRaises(AssertionError):verify(bad)
    def test_false_upper_claim(self):
        bad=copy.deepcopy(self.cert);bad['exact_six_upper_proved']=True
        with self.assertRaises(AssertionError):verify(bad)


if __name__=='__main__':unittest.main()
