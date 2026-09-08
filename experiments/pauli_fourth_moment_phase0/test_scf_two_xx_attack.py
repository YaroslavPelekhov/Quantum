"""C015 saved physical witness and claim-ledger corruption controls."""
import copy
import json
import unittest
from verify_scf_two_xx_attack import verify,DATA


class TwoXXAttackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((DATA/'scf_two_xx_attack_c015.json').read_text())
    def rejected(self,change):
        r=copy.deepcopy(self.report);change(r)
        with self.assertRaises(AssertionError):verify(r)
    def test_independent_bitwise_physical_witnesses(self):
        r=verify(self.report)
        self.assertGreater(r['positive_G8_reevaluated'],3.03)
        self.assertFalse(r['quantum_target_proved'])
    def test_wrong_source_hash(self):self.rejected(lambda r:r.update(source_sha256='0'*64))
    def test_missing_start(self):self.rejected(lambda r:r['runs'].pop(0))
    def test_wrong_sign_basis(self):self.rejected(lambda r:r['free_sign_coordinates'].pop())
    def test_unnormalized_state(self):
        self.rejected(lambda r:r['best'].update(state=[[0,0] for _ in r['best']['state']]))
    def test_false_positive_control(self):self.rejected(lambda r:r['controls']['positive_G8'].update(value=3.0))
    def test_overclaim(self):self.rejected(lambda r:r.update(quantum_target_proved=True))


if __name__=='__main__':unittest.main()
