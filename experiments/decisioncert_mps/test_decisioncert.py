from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

try:
    from .analyze_decisioncert import (
        RESULTS, NUMERICAL_FLOOR, event_angle_interval, expanded_envelope,
        interval_decision, surrogate_values,
    )
except ImportError:  # Direct execution from this directory.
    from analyze_decisioncert import (
        RESULTS, NUMERICAL_FLOOR, event_angle_interval, expanded_envelope,
        interval_decision, surrogate_values,
    )


class FormulaTests(unittest.TestCase):
    def test_identity(self):
        values = surrogate_values([])
        self.assertTrue(all(values[name] == 0.0 for name in ("sum_w", "sqrt_sum_w", "product_trace", "rss_angle")))

    def test_single_weight(self):
        weight = 1e-4
        values = surrogate_values([weight])
        self.assertAlmostEqual(values["sqrt_sum_w"], math.sqrt(weight))
        self.assertAlmostEqual(values["product_trace"], math.sqrt(weight))
        self.assertAlmostEqual(values["rss_angle"], math.sqrt(weight))

    def test_stability_interval(self):
        lower, upper = expanded_envelope([-0.3, -0.2])
        self.assertEqual(interval_decision(lower, upper), -1)
        lower, upper = expanded_envelope([-0.1, 0.2])
        self.assertIsNone(interval_decision(lower, upper))

    def test_event_angle_identity_and_saturation(self):
        q = 0.3
        lower, upper = event_angle_interval(q, 0.0)
        self.assertAlmostEqual(lower, q - NUMERICAL_FLOOR)
        self.assertAlmostEqual(upper, q + NUMERICAL_FLOOR)
        self.assertEqual(event_angle_interval(q, math.pi / 2.0), (0.0, 1.0))

    def test_event_angle_is_inside_additive_trace_interval(self):
        q, angle = 0.2, 0.1
        lower, upper = event_angle_interval(q, angle)
        epsilon = math.sin(angle) + NUMERICAL_FLOOR
        self.assertGreaterEqual(lower + 1e-15, max(0.0, q - epsilon))
        self.assertLessEqual(upper - 1e-15, min(1.0, q + epsilon))


class CompletedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = RESULTS / "decisioncert_summary.json"
        if not path.exists():
            raise unittest.SkipTest("Run exploratory analysis first")
        cls.summary = json.loads(path.read_text(encoding="utf-8"))

    def test_no_heuristic_is_labelled_certificate(self):
        self.assertTrue(all(row["status"] == "heuristic_not_certificate" for row in self.summary["surrogates"].values()))

    def test_stability_has_no_wrong_decision_in_pilot(self):
        self.assertEqual(self.summary["stability"]["ordering_cohorts_wrong"], 0)
        self.assertEqual(self.summary["stability"]["case_decisions_wrong"], 0)

    def test_aggressive_sum_w_is_falsified(self):
        self.assertGreater(self.summary["surrogates"]["sum_w"]["schedule_bks_violations"], 0)

    def test_55q_stability_abstains(self):
        self.assertFalse(self.summary["frozen_55q"]["stable"])
        self.assertIsNone(self.summary["frozen_55q"]["decision"])
        self.assertIn(None, self.summary["frozen_55q"]["marginal_wilson_interval_signs"])

    def test_event_angle_certificate_has_no_wrong_sign(self):
        self.assertEqual(self.summary["event_angle_certificate"]["certified_wrong"], 0)

    def test_heldout_schedule_pair_validation(self):
        heldout = self.summary["heldout_schedule_pair_validation"]
        self.assertTrue(heldout["not_used_to_develop_rule"])
        self.assertEqual(heldout["case_decisions_accepted"], heldout["case_decisions_total"])
        self.assertEqual(heldout["case_decisions_wrong"], 0)


if __name__ == "__main__":
    unittest.main()
