import copy
import json
import unittest

from c020_exact_certificate import DATA
from verify_c039_central_ablations import verify


class CentralAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((DATA / "c039_central_ablations.json").read_text())

    def test_valid(self):
        result = verify(self.report)
        self.assertEqual(result["weighted_instances"], 6225)

    def test_reject_full_polytope_gap(self):
        report = copy.deepcopy(self.report)
        report["records"][0]["full_ratio"] = 1.01
        with self.assertRaises(AssertionError):
            verify(report)

    def test_reject_non_skew_counterexample_corruption(self):
        report = copy.deepcopy(self.report)
        report["skewness_ablation"]["matrix"][0][1] = "-1/2"
        with self.assertRaises(AssertionError):
            verify(report)

    def test_reject_artifact_hash_corruption(self):
        report = copy.deepcopy(self.report)
        key = next(iter(report["artifacts"]))
        report["artifacts"][key] = "0" * 64
        with self.assertRaises(AssertionError):
            verify(report)

    def test_reject_scope_inflation(self):
        report = copy.deepcopy(self.report)
        report["claims"]["experiments_replace_analytic_proof"] = True
        with self.assertRaises(AssertionError):
            verify(report)


if __name__ == "__main__":
    unittest.main()
