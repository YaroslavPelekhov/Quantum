from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from .twin_structural import twin_frontier_profile


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "symmetry_claim_falsification"


class SymmetryClaimFalsificationTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((RESULTS / name).read_text(encoding="utf-8"))

    def test_symmetry_preserving_controls_kill_ansatz_claim(self):
        payload = self.load("symmetry_only.json")
        self.assertTrue(payload["complete"])
        self.assertTrue(payload["qaoa_replay_success"])
        self.assertTrue(payload["seed_stable"])
        self.assertTrue(payload["ansatz_specific_claim_killed"])
        self.assertEqual(sum(len(row["cuts"]) for row in payload["rows"]), 61)
        for row in payload["rows"]:
            expected = row["archived_qaoa_ranks"]
            self.assertTrue(all(profile == expected for profile in row[
                "full_automorphism_haar_ranks"
            ]))
            self.assertTrue(all(profile == expected for profile in row[
                "orbit_phase_ranks"
            ]))
            self.assertTrue(all(profile == expected for profile in row[
                "twin_only_haar_ranks"
            ]))

    def test_twin_bound_explains_every_synthetic_cut(self):
        payload = self.load("twin_bound.json")
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["bound_violations"], 0)
        self.assertTrue(payload["generic_saturation_all_rows"])
        self.assertTrue(payload["seed_stable"])
        self.assertFalse(payload["ansatz_rank_residual_exists"])
        self.assertEqual(sum(len(row["structure"]) for row in payload["rows"]), 84)

    def test_real_transfer_has_no_residual(self):
        payload = self.load("real_bound.json")
        self.assertTrue(payload["complete"])
        self.assertTrue(payload["selection_was_preexisting"])
        self.assertEqual(payload["tested_rank_rows"], 53)
        self.assertEqual(payload["bound_violations"], 0)
        self.assertEqual(payload["residual_rows"], 0)
        self.assertTrue(payload["all_ranks_equal_bound"])

    def test_optimized_baseline_kills_runtime_claim(self):
        payload = self.load("performance.json")
        self.assertTrue(payload["complete"])
        self.assertTrue(payload["exactness_pass"])
        self.assertFalse(payload["old_numeric_claim_survives"])
        self.assertFalse(payload["weaker_practical_speedup_survives"])
        self.assertLess(payload["median_steady_speedup"], 2.0)
        self.assertGreater(payload["representation_compression"], 10.0)

    def test_bound_is_amplitude_blind(self):
        events = np.asarray([1, 2, 4], dtype=np.int64)
        profile = twin_frontier_profile(events, 3, ((0, 1), (2,)))
        self.assertEqual(len(profile), 2)
        self.assertTrue(all(row["twin_structural_bound"] > 0 for row in profile))
        self.assertTrue(all(
            row["twin_structural_bound"] <= row["left_orbit_dimension"]
            for row in profile
        ))

    def test_manifest_hashes(self):
        manifest = self.load("manifest.json")
        self.assertTrue(manifest["complete"])
        self.assertTrue(manifest["claim_rejected"])
        for relative, expected in manifest["files"].items():
            actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
