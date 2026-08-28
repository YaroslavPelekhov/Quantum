from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from analyze_signed_decision import analyze_ordering


class SignedDecisionTests(unittest.TestCase):
    def test_interval_algebra(self) -> None:
        # E_A in [0.08,0.12], E_B in [-0.06,-0.04].  Hence E_B-E_A is
        # centered at -0.15 with radius 0.03.
        delta_mps = -0.4
        center_a, radius_a = 0.1, 0.02
        center_b, radius_b = -0.05, 0.01
        corrected = delta_mps - (center_b - center_a)
        self.assertAlmostEqual(corrected, -0.25)
        self.assertAlmostEqual(corrected - radius_a - radius_b, -0.28)
        self.assertAlmostEqual(corrected + radius_a + radius_b, -0.22)

    def test_archived_r128_improves_sorted_verdict(self) -> None:
        result = analyze_ordering("sorted", None)
        row = next(row for row in result["rows"] if row["residual_bond"] == 128)
        self.assertTrue(row["signed_certified"])
        self.assertFalse(row["legacy_certified"])
        self.assertTrue(row["exact_gap_inside_interval_audit"])

    def test_all_archived_intervals_cover_exact_gap(self) -> None:
        for ordering in ("sorted", "spectral"):
            result = analyze_ordering(ordering, None)
            self.assertTrue(result["rows"])
            self.assertTrue(all(
                row["exact_gap_inside_interval_audit"] for row in result["rows"]
            ))

    def test_asymmetric_grid_is_sound_on_archived_points(self) -> None:
        for ordering in ("sorted", "spectral"):
            result = analyze_ordering(ordering, None)
            self.assertEqual(len(result["asymmetric_grid"]), 9)
            self.assertTrue(all(
                row["exact_gap_inside_interval_audit"]
                for row in result["asymmetric_grid"]
            ))

    def test_frozen_low_bond_sorted_result(self) -> None:
        path = REPO / "results" / "compressed_observable_telescope" / (
            "residual_cot_ibm32_confirm_sorted_adaptive_signed-gap-lowbond.json"
        )
        result = analyze_ordering("sorted", path)
        r32 = next(row for row in result["rows"] if row["residual_bond"] == 32)
        self.assertTrue(r32["signed_certified"])
        self.assertFalse(r32["legacy_certified"])
        self.assertGreater(r32["signed_certificate_margin"], 0.038)
        self.assertEqual(
            sum(x["dense_operator_violations"] for x in result["bond_path_diagnostics"].values()),
            0,
        )

    def test_frozen_low_bond_spectral_transfer(self) -> None:
        path = REPO / "results" / "compressed_observable_telescope" / (
            "residual_cot_ibm32_confirm_spectral_adaptive_signed-gap-lowbond.json"
        )
        result = analyze_ordering("spectral", path)
        r32 = next(row for row in result["rows"] if row["residual_bond"] == 32)
        self.assertTrue(r32["signed_certified"])
        self.assertGreater(r32["signed_certificate_margin"], 0.227)
        self.assertTrue(r32["exact_gap_inside_interval_audit"])


if __name__ == "__main__":
    unittest.main()
