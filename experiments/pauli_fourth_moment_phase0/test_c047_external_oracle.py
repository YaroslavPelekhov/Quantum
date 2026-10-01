import json
import unittest
from pathlib import Path


RESULT = Path(__file__).resolve().parents[2] / "results" / "pauli_fourth_moment_phase0" / "c047_external_oracle.json"


class C047ExternalOracleTests(unittest.TestCase):
    def test_independent_runtime_result(self):
        data = json.loads(RESULT.read_text(encoding="utf-8-sig"))
        self.assertTrue(data["complete"])
        self.assertGreaterEqual(data["root_graphs"], 100)
        self.assertGreaterEqual(data["random_directions"], 3000)
        self.assertEqual(data["inequality_violations"], 0)
        self.assertLessEqual(data["maximum_random_ratio"], 1.0 + 1e-8)
        self.assertLessEqual(data["maximum_tightness_residual"], 2e-8)


if __name__ == "__main__":
    unittest.main()
