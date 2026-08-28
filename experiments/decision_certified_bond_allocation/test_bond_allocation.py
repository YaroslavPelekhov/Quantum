from __future__ import annotations

import hashlib
import json
import unittest

try:
    from .analyze_bond_allocation import RESULTS, REPO, build_summary
except ImportError:
    from analyze_bond_allocation import RESULTS, REPO, build_summary


class BondAllocationTests(unittest.TestCase):
    def test_primary_negative_is_retained(self):
        result = build_summary()["sorted_primary_negative"]
        self.assertFalse(result["certified"])
        self.assertLess(result["certificate_margin"], 0)

    def test_causal_asymmetric_schedule_certifies_and_saves_work(self):
        result = build_summary()["sorted_causal_asymmetric"]
        self.assertTrue(result["certified"])
        self.assertGreater(result["certificate_margin"], 0)
        self.assertGreater(result["paired_cubic_work_saving_fraction"], 0.60)
        self.assertEqual(result["witness_audit"]["tail_monotonic_violations"], 0)
        self.assertEqual(result["witness_audit"]["selected_dense_oracle_violations"], 0)

    def test_spectral_soundness_but_not_resource_optimality_transfers(self):
        result = build_summary()["spectral_frozen_transfer"]
        self.assertTrue(result["certified"])
        self.assertFalse(result["resource_optimality_transferred"])
        self.assertGreater(result["work_multiple_vs_fixed_R128_R128"], 3.0)
        self.assertEqual(result["witness_audit"]["tail_monotonic_violations"], 0)
        self.assertEqual(result["witness_audit"]["selected_dense_oracle_violations"], 0)

    def test_manifest(self):
        manifest = json.loads((RESULTS / "MANIFEST.json").read_text(encoding="utf-8"))
        for section in ("sources", "inputs", "artifacts"):
            for relative, expected in manifest[section].items():
                path = REPO / relative
                self.assertEqual(path.stat().st_size, expected["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected["sha256"])


if __name__ == "__main__":
    unittest.main()
