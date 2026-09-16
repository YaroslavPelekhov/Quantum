"""Mutation tests for the independent C044 proof-hardening verifier."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_c044_proof_hardening import RESULT, verify


class C044ProofHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_frozen_record(self) -> None:
        self.assertEqual(verify(copy.deepcopy(self.payload))["status"], "C044_verified")

    def test_rejects_missing_deletion(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["all_deletions_heredity_audit"]["all_one_vertex_deletions"] -= 1
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_algebra_count_corruption(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["algebraic_parameter_audit"]["admissible_maximum_pairs"] += 1
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_hidden_simplicial_counterexample(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["exact_circulant_clique_audit"]["simplicial_cliques_p_at_least_3"] = 1
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_external_lemma_regression(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["analytic_result"]["external_geometric_lemma_required"] = True
        with self.assertRaises(AssertionError):
            verify(payload)

    def test_rejects_dependency_audit_corruption(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["dependency_audit"]["oriolo_stauffer_theorem_26_checked"] = False
        with self.assertRaises(AssertionError):
            verify(payload)


if __name__ == "__main__":
    unittest.main()
