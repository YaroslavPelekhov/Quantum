from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from .dcsrdt_core import (
    benchmark_pair,
    bks_effect_diagonal,
    decision_conditioned_operator,
    reduced_density,
)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "decision_conditioned_srdt"


class DecisionConditionedSRDTTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(43)
        self.a = rng.normal(size=32) + 1j * rng.normal(size=32)
        self.b = rng.normal(size=32) + 1j * rng.normal(size=32)
        self.a /= np.linalg.norm(self.a)
        self.b /= np.linalg.norm(self.b)

    def test_trace_is_global_effect(self):
        effect = np.asarray([0, 1] * 16, dtype=float)
        operator = decision_conditioned_operator(self.a, self.b, effect, cut=2)
        expected = np.sum(effect * (np.abs(self.b) ** 2 - np.abs(self.a) ** 2))
        self.assertLess(abs(np.trace(operator).real - expected), 1e-12)
        self.assertLess(np.linalg.norm(operator - operator.conj().T), 1e-12)

    def test_identity_effect_reduces_to_srdt(self):
        operator = decision_conditioned_operator(
            self.a, self.b, np.ones(self.a.size), cut=2
        )
        expected = reduced_density(self.b, 2) - reduced_density(self.a, 2)
        self.assertLess(np.linalg.norm(operator - expected), 1e-12)

    def test_spectral_tail_is_exact_and_optimal_against_controls(self):
        effect = np.asarray(([0, 0, 1, 1] * 8), dtype=float)
        result = benchmark_pair(self.a, self.b, effect, cut=2, ranks=(1, 2, 3))
        for row in result["rows"]:
            target = row["methods"]["decision_conditioned"]
            self.assertAlmostEqual(target["trace_norm_bound"], target["spectral_tail"])
            self.assertLessEqual(target["absolute_error"], target["trace_norm_bound"] + 1e-12)
            for control in ("srdt_basis", "state_averaged_basis"):
                self.assertLessEqual(
                    target["trace_norm_bound"],
                    row["methods"][control]["trace_norm_bound"] + 1e-12,
                )

    def test_vectorized_bks_effect(self):
        scorer = {
            "constant_selected": 0,
            "weights": [1, 1, 1],
            "forbidden": [[3, 3]],
            "impossible": False,
            "bks": 2,
        }
        effect = bks_effect_diagonal(scorer)
        self.assertEqual(np.flatnonzero(effect).tolist(), [5, 6])

    def test_frozen_development_and_transfer_verdicts(self):
        development = json.loads(
            (RESULTS / "development.json").read_text(encoding="utf-8")
        )
        transfer = json.loads(
            (RESULTS / "transfer.json").read_text(encoding="utf-8")
        )
        self.assertTrue(development["success"])
        self.assertTrue(transfer["success"])
        self.assertEqual(development["passed_rows"], 4)
        self.assertEqual(transfer["passed_rows"], 4)
        self.assertEqual(development["protocol_sha256"], transfer["protocol_sha256"])

    def test_manifest_hashes(self):
        manifest = json.loads(
            (RESULTS / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["development_success"])
        self.assertTrue(manifest["transfer_success"])
        for relative, expected in manifest["files"].items():
            actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
