import copy
import json
import unittest

import verify_c041_density_coupling_stress as verifier


class DensityCouplingStressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(verifier.REPORT.read_text(encoding="utf-8"))

    def test_valid(self):
        self.assertEqual(verifier.verify(copy.deepcopy(self.report))["coupling_instances"], 28)

    def test_reject_density_ordering_corruption(self):
        altered = copy.deepcopy(self.report)
        altered["density_records"][0]["odd9_ratio"] = 2
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_missing_stress_case(self):
        altered = copy.deepcopy(self.report)
        altered["density_records"] = altered["density_records"][:-1]
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_coupling_formula_corruption(self):
        altered = copy.deepcopy(self.report)
        altered["coupling_ablations"][5]["matching"] += 0.1
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_artifact_hash_corruption(self):
        altered = copy.deepcopy(self.report)
        key = next(iter(altered["artifacts"]))
        altered["artifacts"][key] = "0" * 64
        with self.assertRaises(AssertionError):
            verifier.verify(altered)


if __name__ == "__main__":
    unittest.main()
