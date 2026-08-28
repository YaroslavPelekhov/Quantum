from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from analyze_reset_intervention import POLICY_ORDER, analyze_ordering, policy_work
from run_reset_intervention import intervention_configs


class ResetInterventionTests(unittest.TestCase):
    def test_schedules_cover_domain_and_have_equal_work(self) -> None:
        configs = intervention_configs()
        self.assertEqual(tuple(config["key"] for config in configs), POLICY_ORDER)
        works = []
        for config in configs:
            positions = []
            for start, end, bond in config["schedule"]:
                positions.extend(range(start, end + 1))
                self.assertIn(bond, (32, 128))
            self.assertEqual(positions, list(range(1, 556)))
            works.append(policy_work(config["schedule"]))
        self.assertLess(max(works) - min(works), 1e-15)

    def test_artifacts_when_present(self) -> None:
        paths = [REPO / "results" / "signed_decision_cot" / f"reset_intervention_{o}.json"
                 for o in ("sorted", "spectral")]
        if not all(path.exists() for path in paths):
            self.skipTest("Intervention artifacts not executed yet")
        for ordering in ("sorted", "spectral"):
            result = analyze_ordering(ordering)
            self.assertEqual(result["dense_violations"], 0)
            self.assertTrue(all(row["exact_gap_inside_interval_audit"] for row in result["pair_rows"]))


if __name__ == "__main__":
    unittest.main()

