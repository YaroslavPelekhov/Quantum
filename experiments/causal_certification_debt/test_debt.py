from __future__ import annotations

import hashlib
import json
import unittest

try:
    from .analyze_debt import REPO, RESULTS, build_summary
except ImportError:
    from analyze_debt import REPO, RESULTS, build_summary


class DebtIdentityTests(unittest.TestCase):
    def test_executed_rank_two_identities(self):
        summary = build_summary()
        self.assertEqual({row["rank"] for row in summary["cases"]}, {2})
        self.assertLess(summary["maximum_recurrence_error"], 1e-15)
        self.assertLess(summary["maximum_identity_error"], 1e-12)
        self.assertLess(summary["maximum_correction_reconstruction_error"], 1e-12)

    def test_sorted_lr_debt_dominates_correction(self):
        row = next(
            item for item in build_summary()["cases"]
            if item["label"] == "sorted_rescue_lr"
        )
        self.assertFalse(row["cap_active"])
        self.assertGreater(row["tail_fraction_of_correction"], 0.90)

    def test_manifest(self):
        manifest = json.loads((RESULTS / "MANIFEST.json").read_text(encoding="utf-8"))
        for section in ("sources", "inputs", "artifacts"):
            for relative, expected in manifest[section].items():
                path = REPO / relative
                self.assertEqual(path.stat().st_size, expected["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected["sha256"])


if __name__ == "__main__":
    unittest.main()
