from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

import numpy as np

try:
    from .run_observable_telescope import RESULTS, bks_basis_indices, event_probability
except ImportError:  # Direct execution from this directory.
    from run_observable_telescope import RESULTS, bks_basis_indices, event_probability


class FormulaTests(unittest.TestCase):
    def test_rank_one_event_probability(self):
        state = np.asarray([1, 1j], dtype=np.complex128) / np.sqrt(2)
        vectors = np.asarray([[1], [0]], dtype=np.complex128)
        self.assertAlmostEqual(event_probability(state, vectors), 0.5)

    def test_static_bks_projector(self):
        scorer = {"constant_selected": 0, "weights": [1, 1], "forbidden": [], "impossible": False, "bks": 2}
        self.assertEqual(bks_basis_indices(scorer), [3])


class CompletedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        summary_path = RESULTS / "summary.json"
        pair_path = RESULTS / "pair_rows.json"
        if not summary_path.exists():
            raise unittest.SkipTest("Run telescope pilot first")
        cls.summary = json.loads(summary_path.read_text(encoding="utf-8"))
        cls.pairs = json.loads(pair_path.read_text(encoding="utf-8"))["rows"]

    def test_telescope_identity_and_bound(self):
        self.assertLess(self.summary["maximum_telescope_identity_error"], 1e-9)
        self.assertLessEqual(self.summary["maximum_bound_violation"], 1e-9)
        self.assertLess(self.summary["maximum_frozen_rankcert_regression_error"], 1e-12)

    def test_no_wrong_certificate(self):
        self.assertFalse([row for row in self.pairs if row["certified"] and not row["correct_sign"]])

    def test_unique_pairs(self):
        keys = [(row["case"], row["setting"], row["ordering"]) for row in self.pairs]
        self.assertEqual(len(keys), len(set(keys)))

    def test_strict_coverage_improves_on_same_cohort(self):
        self.assertEqual(self.summary["accumulated_angle_certified_same_cohort"], 4)
        self.assertEqual(self.summary["telescope_certified"], 14)
        self.assertEqual(self.summary["newly_certified_over_accumulated_angle"], 10)


class IBM32ArtifactTests(unittest.TestCase):
    def test_targeted_resource_ladder(self):
        expected = {
            "released": False,
            "confirm": True,
            "bond128": True,
            "cutoff1e-4": True,
            "cutoff1e-5": True,
        }
        for setting, should_certify in expected.items():
            path = RESULTS / f"ibm32_{setting}_sorted.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(payload["complete"])
            self.assertEqual(payload["pair"]["certified"], should_certify)
            self.assertTrue(payload["pair"]["correct_sign"])
            for row in payload["rows"]:
                self.assertLess(row["telescope_identity_error"], 1e-8)
                self.assertLess(row["frozen_rankcert_regression_error"], 1e-6)
                self.assertLessEqual(
                    row["actual_bks_error"], row["observable_telescope_bound"] + 1e-8
                )


class ManifestTests(unittest.TestCase):
    def test_recorded_hashes(self):
        manifest = json.loads((RESULTS / "MANIFEST.json").read_text(encoding="utf-8"))
        repo = Path(__file__).resolve().parents[2]
        for section in ("sources", "artifacts"):
            for relative, record in manifest[section].items():
                path = repo / relative
                self.assertEqual(path.stat().st_size, record["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])


if __name__ == "__main__":
    unittest.main()
