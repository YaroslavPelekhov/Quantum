import copy
import json
import unittest
from verify_scf_rectangular_gram_bridge import DATA,verify,verify_record,verify_envelope


class RectangularGramBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((DATA/'scf_rectangular_gram_bridge.json').read_text())

    def test_all_exact_family_identities_and_target(self):
        self.assertEqual(verify(self.report)['target_exact_beta'],3)

    def test_corrupt_cycle_phase_rejected(self):
        row=copy.deepcopy(self.report['records'][1])
        row['central_involutions'][0]['phase']*=-1
        with self.assertRaises(AssertionError): verify_record(row)

    def test_corrupt_Gram_entry_rejected(self):
        row=copy.deepcopy(self.report['records'][1])
        row['Gram_B'][1][0]['central_index']=None
        with self.assertRaises(AssertionError): verify_record(row)

    def test_corrupt_transfer_coefficient_rejected(self):
        row=copy.deepcopy(self.report['records'][1])
        row['transfer_coefficients'][1][0]['coefficient']+=1
        with self.assertRaises(AssertionError): verify_record(row)

    def test_known_G8_invalid_graph_rejected(self):
        row=copy.deepcopy(self.report['records'][0])
        row['graph6']='GCrdrk'
        with self.assertRaises(AssertionError): verify_record(row)

    def test_corrupt_target_mapping_rejected(self):
        report=copy.deepcopy(self.report)
        report['family_to_target_mapping'][0]=report['family_to_target_mapping'][1]
        with self.assertRaises(AssertionError): verify(report)

    def test_unsupported_all_weights_claim_rejected(self):
        report=copy.deepcopy(self.report)
        report['all_weights_claim']=True
        with self.assertRaises(AssertionError): verify(report)

    def test_exact_envelope_factorization(self):
        verify_envelope()


if __name__=='__main__': unittest.main()
