from __future__ import annotations

import math
import json
import tempfile
import unittest
from pathlib import Path

from certificate import accumulated_angle_certificate, ranking_certificate, validated_weight
from parse_aer_mps_log import parse_mps_log, printed_double_upper_bound
from rankcert_inputs import CASES, exact_effects, load_specs, sha256
from run_rankcert_exact_cases import load_completed_rows


class CertificateTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(accumulated_angle_certificate([]).epsilon, 0.0)

    def test_single_truncation(self):
        for weight in (1e-12, 1e-4, 0.25, 1.0):
            self.assertAlmostEqual(accumulated_angle_certificate([weight]).epsilon, math.sqrt(weight), places=14)

    def test_monotonicity(self):
        first = accumulated_angle_certificate([1e-4]).epsilon
        second = accumulated_angle_certificate([1e-4, 1e-6]).epsilon
        self.assertGreaterEqual(second, first)

    def test_saturation(self):
        result = accumulated_angle_certificate([0.5, 0.5])
        self.assertTrue(result.saturated)
        self.assertEqual(result.epsilon, 1.0)

    def test_weight_numerical_safety(self):
        self.assertEqual(validated_weight(-1e-14), 0.0)
        self.assertEqual(validated_weight(1 + 1e-14), 1.0)
        for value in (-1e-4, 1.1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                validated_weight(value)

    def test_ranking_interval_logic(self):
        self.assertTrue(ranking_certificate(0.1, 0.01, 0.2, 0.01)["certified"])
        self.assertFalse(ranking_certificate(0.1, 0.06, 0.2, 0.05)["certified"])

    def test_analytic_bound(self):
        weight = 1e-4
        epsilon = accumulated_angle_certificate([weight]).epsilon
        trace_distance = math.sqrt(weight)
        event_error = weight
        self.assertGreaterEqual(epsilon + 1e-15, trace_distance)
        self.assertGreaterEqual(epsilon + 1e-15, event_error)


class ParserTests(unittest.TestCase):
    def test_parser_preserves_all_values_and_context(self):
        log = "{discarded_value=0.0001, I0:cx on qubits 0,1, BD=[2], discarded_value=2e-06, I1:rzz on qubits 1,2, BD=[1 3], }"
        parsed = parse_mps_log(log)
        self.assertEqual(parsed["discarded_weights"], [1e-4, 2e-6])
        self.assertEqual(parsed["number_of_truncations"], 2)
        self.assertEqual(parsed["max_bond_seen"], 3)
        self.assertEqual(parsed["events"][0]["instruction_index"], 0)
        self.assertEqual(parsed["events"][1]["instruction_index"], 1)
        self.assertEqual(tuple(parsed["events"][1]["qubits"]), (1, 2))
        self.assertGreater(parsed["certificate_weight_upper_bounds"][0], 1e-4)
        self.assertAlmostEqual(printed_double_upper_bound(1e-4), 0.0001000005, places=15)

    def test_empty_log(self):
        parsed = parse_mps_log("{}")
        self.assertEqual(parsed["discarded_weights"], [])
        self.assertEqual(parsed["number_of_truncations"], 0)

    def test_orphan_value_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_mps_log("{discarded_value=1e-6}")


class FrozenInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = load_specs()

    def test_exact_effect_reproduction(self):
        effects = exact_effects(self.specs)
        self.assertEqual(len(effects), 2 * len(CASES))
        self.assertTrue(all(row["rounded_agreement"] for row in effects))

    def test_circuit_hash_consistency(self):
        for row in self.specs:
            self.assertEqual(sha256(Path(row["circuit_file"])), row["circuit_sha256"])

    def test_probabilities_in_range(self):
        for row in self.specs:
            for name in ("bks_rate", "near_bks_rate", "feasible_rate", "quality_mass"):
                self.assertGreaterEqual(row["exact_metrics"][name], 0.0)
                self.assertLessEqual(row["exact_metrics"][name], 1.0 + 1e-12)


class ResumeTests(unittest.TestCase):
    def test_complete_rows_resume_and_incomplete_rows_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {
                "stage": "rankcert_aer_schedule_run", "case": "karate",
                "setting": "released", "method": "published_lr", "ordering": "sorted",
            }
            (root / "complete.json").write_text(json.dumps({**base, "complete": True}), encoding="utf-8")
            (root / "partial.json").write_text(json.dumps({**base, "ordering": "spectral", "complete": False}), encoding="utf-8")
            rows = load_completed_rows(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["ordering"], "sorted")


class CompletedArtifactTests(unittest.TestCase):
    def test_all_certified_exact_rankings_are_correct(self):
        path = Path(__file__).resolve().parents[2] / "results" / "rankcert_mps" / "rankcert_pair_rows.json"
        if not path.exists():
            self.skipTest("Completed pair artifact not present")
        rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
        self.assertFalse([row for row in rows if row["certified"] and not row["correct_sign"]])
        self.assertEqual(len({(row["case"], row["setting"], row["ordering"]) for row in rows}), len(rows))


if __name__ == "__main__":
    unittest.main()
