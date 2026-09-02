from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[2]
PROTOCOL = REPO / "experiments" / "cmrt_phase0" / "protocol.json"
RESULT = REPO / "results" / "cmrt_phase0" / "phase0_results.json"


@unittest.skipUnless(RESULT.exists(), "full CMRT result has not been generated")
class Phase0IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_result_is_bound_to_frozen_protocol(self):
        self.assertEqual(
            self.result["protocol_sha256"], hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        )
        self.assertEqual(self.result["protocol_status_before_run"], "FROZEN_NOT_RUN")

    def test_whole_graph_split_and_cohort_sizes(self):
        cohort = self.result["cohort"]
        self.assertEqual(cohort["graph_count"], 36)
        self.assertEqual(cohort["calibration_graphs"], 24)
        self.assertEqual(cohort["test_graphs"], 12)
        self.assertEqual(cohort["base_rows"], 108)
        calibration = {
            row["graph_id"] for row in cohort["graphs"] if row["split"] == "calibration"
        }
        test = {row["graph_id"] for row in cohort["graphs"] if row["split"] == "test"}
        self.assertFalse(calibration & test)

    def test_binding_decision_is_negative_and_complete(self):
        decision = self.result["decision"]
        self.assertEqual(decision["terminal_label"], "KILL_CMRT_AS_ASTAR_SOURCE")
        self.assertFalse(decision["all_gates_passed"])
        self.assertEqual(decision["total_gate_count"], 10)
        self.assertEqual(decision["passed_gate_count"], 4)
        self.assertEqual(len(decision["failed_gates"]), 6)

    def test_exact_equivalence_and_no_hidden_ties(self):
        self.assertLessEqual(
            self.result["audit"]["maximum_exact_equivalence_gap_error"], 1e-10
        )
        for row in self.result["rows"]:
            for hardware in row["primary_hardware_surrogates"]:
                self.assertGreater(abs(hardware["gap"]), 1e-15)
            self.assertGreater(abs(row["shift_noise"]["gap"]), 1e-15)

    def test_shot_audit_is_nonbinding(self):
        audit = self.result["shot_audit"]
        self.assertFalse(audit["binding"])
        self.assertIn("descriptive", audit["interval_scope"])


if __name__ == "__main__":
    unittest.main()
