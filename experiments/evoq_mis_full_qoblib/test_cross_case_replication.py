import json
import unittest
import csv

import numpy as np

import run_cross_case_replication as cross


class CrossCaseReplicationTests(unittest.TestCase):
    def test_frozen_design_counts(self):
        self.assertEqual(len(cross.CASES), 4)
        self.assertEqual(len(cross.ALL_CASES), 5)
        self.assertEqual(len(cross.SETTINGS), 5)
        self.assertEqual(cross.EXPECTED_NEW_PER_BACKEND, 120)
        self.assertEqual(cross.EXPECTED_TOTAL, 300)

    def test_cases_match_completed_exact_artifact(self):
        artifact = json.loads(cross.EXTERNAL_EXACT.read_text(encoding="utf-8"))
        rows = artifact["rows"]
        for case in cross.CASES:
            for ordering in cross.ORDERINGS:
                cohort = {
                    row["method"]: row
                    for row in rows
                    if row["case"] == case["name"] and row["ordering"] == ordering
                }
                self.assertEqual(set(cohort), set(cross.METHOD_NAMES))
                effect = (
                    cohort["prior_matched_random"]["metrics"]["bks_rate"]
                    - cohort["published_lr"]["metrics"]["bks_rate"]
                )
                self.assertAlmostEqual(effect, case["expected_effect"], places=8)

    def test_static_scorer_and_state_comparison(self):
        scorer = {
            "constant_selected": 0,
            "weights": [1, 1],
            "forbidden": [[3, 3]],
            "impossible": False,
            "bks": 1,
        }
        state = np.full(4, 0.5 + 0j, dtype=np.complex128)
        metrics, accumulator = cross.audit.score_state(state, scorer)
        comparison = cross.audit.compare_states(state, state.copy())
        self.assertEqual(metrics["feasible_rate"], 0.75)
        self.assertEqual(metrics["bks_rate"], 0.5)
        self.assertEqual(accumulator["basis_states"], 4)
        self.assertAlmostEqual(comparison["state_fidelity"], 1.0, places=15)
        self.assertEqual(comparison["total_variation_distance"], 0.0)

    def test_tvd_event_effect_certificate_identity(self):
        exact_effect = -0.2
        approximate_effect = -0.17
        bound = 0.01 + 0.02
        self.assertLessEqual(abs(approximate_effect - exact_effect), bound + 1e-15)
        self.assertGreater(abs(exact_effect), bound)
        self.assertEqual(cross.sign(exact_effect), cross.sign(approximate_effect))

    def test_completed_analysis_has_frozen_cohort_invariants(self):
        if not cross.ANALYSIS.exists():
            self.skipTest("Completed analysis artifact is not present")
        analysis = json.loads(cross.ANALYSIS.read_text(encoding="utf-8"))
        self.assertTrue(analysis["complete"])
        self.assertEqual(len(analysis["summaries"]), 100)
        self.assertEqual(len(analysis["cross_backend"]), 50)
        self.assertEqual(analysis["global"]["tvd_bounds_valid"], 100)
        certified = [
            row for row in analysis["summaries"]
            if row["exact_margin_tvd_certified"]
        ]
        self.assertEqual(len(certified), 77)
        self.assertTrue(all(row["matched_sign_correct"] for row in certified))

    def test_paper_summary_matches_analysis(self):
        table = cross.RESULTS / "paper_summary.csv"
        if not table.exists() or not cross.ANALYSIS.exists():
            self.skipTest("Paper summary artifacts are not present")
        analysis = json.loads(cross.ANALYSIS.read_text(encoding="utf-8"))
        expected = {row["case"]: row for row in analysis["cases"]}
        with table.open(encoding="utf-8", newline="") as handle:
            actual = {row["case"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(actual), set(expected))
        for case, row in expected.items():
            self.assertEqual(int(actual[case]["sign_correct"]), row["sign_correct"])
            self.assertEqual(int(actual[case]["tvd_certified"]), row["exact_margin_certified"])


if __name__ == "__main__":
    unittest.main()
