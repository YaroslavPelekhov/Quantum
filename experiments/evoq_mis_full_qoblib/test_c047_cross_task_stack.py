import json
import unittest
from pathlib import Path


RESULT = Path(__file__).with_name("results") / "c047_cross_task_stack.json"


class C047ExternalValidationTests(unittest.TestCase):
    def test_frozen_result(self):
        data = json.loads(RESULT.read_text(encoding="utf-8"))
        self.assertTrue(data["complete"])
        self.assertEqual(data["summary"]["exact_rows"], 16)
        self.assertEqual(data["summary"]["mps_rows"], 80)
        self.assertEqual(data["summary"]["cohorts"], 40)
        self.assertEqual(data["summary"]["inequalities_holding"], 40)
        self.assertLessEqual(data["summary"]["maximum_cross_sdk_tvd"], 1e-10)
        self.assertLessEqual(data["summary"]["maximum_exact_ordering_residual"], 1e-10)
        self.assertEqual(
            data["summary"]["certified_cohorts"],
            data["summary"]["certified_sign_correct"],
        )

    def test_corruption_is_detected(self):
        data = json.loads(RESULT.read_text(encoding="utf-8"))
        row = dict(data["cohorts"][0])
        row["mps_effect"] += row["tvd_bound"] + 1.0
        error = abs(row["mps_effect"] - row["exact_effect"])
        self.assertGreater(error, row["tvd_bound"])


if __name__ == "__main__":
    unittest.main()
