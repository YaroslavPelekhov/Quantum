from __future__ import annotations

import json
import hashlib
import unittest

try:
    from .analyze_allocation import RESULTS, analyze
except ImportError:
    from analyze_allocation import RESULTS, analyze


class AllocationTests(unittest.TestCase):
    def test_complete_grid_and_soundness(self):
        result = analyze("sorted")
        self.assertEqual(result["candidate_pairs"], 25)
        self.assertEqual(result["wrong_certificates_audit_only"], 0)
        self.assertEqual(result["unsound_pair_inputs_audit_only"], 0)

    def test_joint_optimum_beats_symmetric(self):
        result = analyze("sorted")
        oracle = result["oracle_minimum_cost_certified"]
        symmetric = result["best_symmetric_certified"]
        self.assertEqual((oracle["lr_setting"], oracle["mr_setting"]), ("released", "confirm"))
        self.assertEqual((symmetric["lr_setting"], symmetric["mr_setting"]), ("confirm", "confirm"))
        self.assertGreater(result["simulation_time_saving_fraction"], 0.10)

    def test_serialized_result_if_present(self):
        path = RESULTS / "summary.json"
        if not path.exists():
            self.skipTest("Run analyzer first")
        summary = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(summary["selection_uses_exact_values"])
        self.assertTrue(summary["complete"])
        if "heldout_spectral" in summary:
            heldout = summary["heldout_spectral"]
            self.assertTrue(heldout["allocation_was_frozen_before_execution"])
            self.assertTrue(heldout["frozen_design_allocation"]["certified"])
            self.assertTrue(heldout["frozen_design_allocation"]["correct_direction_audit_only"])
            self.assertGreater(heldout["simulation_time_saving_fraction"], 0.07)

    def test_manifest_hashes_if_present(self):
        path = RESULTS / "MANIFEST.json"
        if not path.exists():
            self.skipTest("Run analyzer first")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        repo = RESULTS.parents[1]
        for section in ("sources", "inputs", "artifacts"):
            for relative, expected in manifest[section].items():
                target = repo / relative
                self.assertEqual(target.stat().st_size, expected["bytes"])
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), expected["sha256"])


if __name__ == "__main__":
    unittest.main()
