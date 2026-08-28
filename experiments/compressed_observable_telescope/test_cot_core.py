from __future__ import annotations

import math
import json
import unittest

import numpy as np

try:
    from .cot_core import (
        compress_statevector_ttsvd,
        compress_vector_ttsvd_unnormalized,
        group_aer_weights_by_instruction,
        grouped_angle_and_effective_weight,
        projector_operator_norm_difference,
    )
except ImportError:
    from cot_core import (
        compress_statevector_ttsvd,
        compress_vector_ttsvd_unnormalized,
        group_aer_weights_by_instruction,
        grouped_angle_and_effective_weight,
        projector_operator_norm_difference,
    )


class CoreTests(unittest.TestCase):
    def test_aer_internal_swap_grouping(self):
        log = "{I0:rzz, discarded_value=1e-4, internal_swap on qubits 2,1, discarded_value=2e-4, I1:rzz,}"
        groups = group_aer_weights_by_instruction(log)
        self.assertEqual(groups[0], [])
        self.assertEqual(len(groups[1]), 2)
        self.assertGreater(groups[1][0], 1e-4)

    def test_grouped_radius_single_truncation(self):
        angle, effective, radius = grouped_angle_and_effective_weight([0.04])
        self.assertAlmostEqual(angle, math.asin(0.2))
        self.assertAlmostEqual(effective, 0.04)
        self.assertAlmostEqual(radius, 0.4)

    def test_ttsvd_product_state_exact(self):
        state = np.zeros(16, dtype=np.complex128)
        state[9] = 1.0
        compressed, info = compress_statevector_ttsvd(state, 1)
        self.assertTrue(np.allclose(compressed, state))
        self.assertLess(info["compression_angle"], 1e-12)

    def test_ttsvd_bell_requires_bond_two(self):
        state = np.asarray([1, 0, 0, 1], dtype=np.complex128) / math.sqrt(2)
        exact, _ = compress_statevector_ttsvd(state, 2)
        approximate, _ = compress_statevector_ttsvd(state, 1)
        self.assertTrue(np.allclose(exact, state))
        self.assertAlmostEqual(abs(np.vdot(state, approximate)), 1 / math.sqrt(2))

    def test_unnormalized_ttsvd_preserves_exact_vector(self):
        vector = np.zeros(16, dtype=np.complex128)
        vector[3] = 2.0 - 1.5j
        approximate, info = compress_vector_ttsvd_unnormalized(vector, 1)
        self.assertTrue(np.allclose(approximate, vector))
        self.assertLess(info["discarded_norm_upper_bound"], 1e-12)

    def test_unnormalized_ttsvd_error_is_certified(self):
        random = np.random.default_rng(142857)
        vector = random.normal(size=64) + 1j * random.normal(size=64)
        vector *= 0.37 / np.linalg.norm(vector)
        approximate, info = compress_vector_ttsvd_unnormalized(vector, 2)
        actual = np.linalg.norm(vector - approximate)
        self.assertLessEqual(actual, info["discarded_norm_upper_bound"] + 1e-12)
        self.assertNotAlmostEqual(np.linalg.norm(approximate), 1.0)

    def test_projector_norm_rank_one(self):
        exact = np.asarray([[1], [0]], dtype=np.complex128)
        approximate = np.asarray([[1], [1]], dtype=np.complex128) / math.sqrt(2)
        value = projector_operator_norm_difference(exact, approximate)
        self.assertAlmostEqual(value, 1 / math.sqrt(2))

    def test_proposed_holder_bound(self):
        exact_vector = np.asarray([1, 0], dtype=np.complex128)
        approximate_vector = np.asarray([1, 1], dtype=np.complex128) / math.sqrt(2)
        exact_observable = np.outer(exact_vector, exact_vector.conj())
        approximate_observable = np.outer(approximate_vector, approximate_vector.conj())
        rho_post = np.asarray([[0.6, 0.2], [0.2, 0.4]], dtype=np.complex128)
        rho_pre = np.asarray([[0.5, 0.0], [0.0, 0.5]], dtype=np.complex128)
        delta = rho_post - rho_pre
        eta = np.linalg.norm(exact_observable - approximate_observable, ord=2)
        lhs = abs(np.trace(exact_observable @ delta))
        rhs = abs(np.trace(approximate_observable @ delta)) + eta * np.linalg.norm(delta, ord="nuc")
        self.assertLessEqual(lhs, rhs + 1e-14)


class CompletedArtifactTests(unittest.TestCase):
    def test_ibm32_fixed_negative_and_adaptive_positive_verdict(self):
        root = __import__("pathlib").Path(__file__).resolve().parents[2]
        summary = json.loads(
            (root / "results" / "compressed_observable_telescope" / "summary.json").read_text(encoding="utf-8")
        )
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["forward_group_bound_violations"], 0)
        self.assertFalse(summary["fixed_bond_8_64_certificate_survives"])
        self.assertTrue(summary["adaptive_certificate_survives"])
        self.assertTrue(all(
            row["paired_operator_correction"] > abs(summary["mps_gap"])
            for row in summary["bond_ladder"]
        ))
        adaptive = {
            row["residual_backward_bond"]: row
            for row in summary["adaptive_pair_rows"]
        }
        self.assertFalse(adaptive[128]["certified"])
        self.assertTrue(adaptive[256]["certified"])
        self.assertGreater(adaptive[256]["certificate_margin"], 0.0)
        heldout = {
            row["residual_backward_bond"]: row
            for row in summary["spectral_heldout_pair_rows"]
        }
        self.assertTrue(summary["spectral_heldout_protocol_frozen"])
        self.assertTrue(heldout[256]["certified"])
        self.assertGreater(heldout[256]["certificate_margin"], 0.19)


if __name__ == "__main__":
    unittest.main()
