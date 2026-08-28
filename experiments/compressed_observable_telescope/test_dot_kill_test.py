from __future__ import annotations

import json
import unittest
from pathlib import Path


class DOTArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.summary = json.loads(
            (root / "results" / "dot_mps_kill_test" / "summary.json").read_text(encoding="utf-8")
        )

    def test_frozen_primary_is_a_recorded_negative(self):
        self.assertTrue(self.summary["complete"])
        self.assertFalse(self.summary["protocol_primary_passed"])
        self.assertLess(self.summary["primary_improvement_factor"], 1.1)
        self.assertGreater(self.summary["primary_mass_importance_spearman"], 0.99)

    def test_exploratory_sweep_does_not_override_primary(self):
        self.assertEqual(self.summary["exploratory_tenfold_successes"], 0)
        self.assertLess(self.summary["maximum_exploratory_improvement_factor_chi40"], 1.1)
        self.assertEqual(len(self.summary["sensitivity_rows"]), 7)


if __name__ == "__main__":
    unittest.main()
