import copy
import json
import unittest
from verify_scf_cross_claw_gate import DATA,verify,verify_record,verify_dephasing


class CrossClawGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'scf_cross_claw_gate.json').read_text())

    def test_independent_exhaustive_template_and_corpus(self):
        self.assertEqual(verify(self.report)['exhaustive_counts']['graphs'],16384)

    def test_corrupt_parity_rejected(self):
        row=copy.deepcopy(self.report['records'][0])
        row['parity']['left'][0]['J_odd']=not row['parity']['left'][0]['J_odd']
        with self.assertRaises(AssertionError): verify_record(row)

    def test_omitted_local_claw_rejected(self):
        row=copy.deepcopy(self.report['controls'][-1])
        row['local_claws']['left']=[]
        with self.assertRaises(AssertionError): verify_record(row)

    def test_corrupt_template_hash_rejected(self):
        report=copy.deepcopy(self.report)
        report['exhaustive_template']['acceptance_bitstream_sha256']='0'*64
        with self.assertRaises(AssertionError): verify(report)

    def test_unsupported_quantum_claim_rejected(self):
        report=copy.deepcopy(self.report)
        report['quantum_compatibility_proved']=True
        with self.assertRaises(AssertionError): verify(report,exhaustive=False)

    def test_exact_dephasing_control(self):
        verify_dephasing(self.report['dephasing_control'])

    def test_corrupt_dephasing_state_rejected(self):
        c=copy.deepcopy(self.report['dephasing_control'])
        c['coherent_integer_state'][0]=2
        with self.assertRaises(AssertionError): verify_dephasing(c)


if __name__=='__main__': unittest.main()
