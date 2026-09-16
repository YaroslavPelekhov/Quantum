import copy
import json
import unittest

import verify_c040_scaled_ablations as verifier


class ScaledAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(verifier.REPORT.read_text(encoding="utf-8"))

    def test_valid(self):
        self.assertEqual(verifier.verify(copy.deepcopy(self.report))["weighted_instances"], 720)

    def test_reject_nonmonotone_baseline(self):
        altered = copy.deepcopy(self.report)
        altered["records"][0]["odd9_ratio"] = altered["records"][0]["degree_ratio"] + 1
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_false_full_blossom(self):
        altered = copy.deepcopy(self.report)
        altered["full_blossom_spot_checks"][0]["ratio"] = 1.01
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_structured_gap_corruption(self):
        altered = copy.deepcopy(self.report)
        altered["structured_ablations"][-1]["odd9_ratio"] = 1.0
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_non_skew_scaling_corruption(self):
        altered = copy.deepcopy(self.report)
        altered["non_skew_scaling"][-1]["violation_ratio"] = 1.0
        with self.assertRaises(AssertionError):
            verifier.verify(altered)

    def test_reject_artifact_corruption(self):
        altered = copy.deepcopy(self.report)
        key = next(iter(altered["artifacts"]))
        altered["artifacts"][key] = "0" * 64
        with self.assertRaises(AssertionError):
            verifier.verify(altered)


if __name__ == "__main__":
    unittest.main()
