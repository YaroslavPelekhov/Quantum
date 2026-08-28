from __future__ import annotations

import unittest

import numpy as np

from .srdt_core import (
    reduced_pair,
    state_averaged_projection,
    synthetic_metrics,
    synthetic_pair,
    trace_norm_hermitian,
    truncate_hermitian_absolute,
)
from .contrast_augmented import common_project_pair


class SignedReducedDensityTests(unittest.TestCase):
    def test_contrast_augmented_full_rank_is_identity(self):
        rng = np.random.default_rng(19)
        state_a = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_b = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_a /= np.linalg.norm(state_a)
        state_b /= np.linalg.norm(state_b)
        projected_a, projected_b, _ = common_project_pair(
            state_a, state_b, sites=4, cut=2, rank=4, alpha=0.25
        )
        self.assertAlmostEqual(abs(np.vdot(state_a, projected_a)), 1.0, places=12)
        self.assertAlmostEqual(abs(np.vdot(state_b, projected_b)), 1.0, places=12)

    def test_contrast_augmented_target_is_positive(self):
        rng = np.random.default_rng(23)
        state_a = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_b = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_a /= np.linalg.norm(state_a)
        state_b /= np.linalg.norm(state_b)
        projected_a, projected_b, info = common_project_pair(
            state_a, state_b, sites=4, cut=2, rank=2, alpha=0.25
        )
        self.assertAlmostEqual(np.linalg.norm(projected_a), 1.0, places=12)
        self.assertAlmostEqual(np.linalg.norm(projected_b), 1.0, places=12)
        self.assertGreater(info["retained_norm_a"], 0.0)
        self.assertGreater(info["retained_norm_b"], 0.0)

    def test_synthetic_contrast_has_exact_rank_two(self):
        for local_qubits in range(2, 7):
            row = synthetic_metrics(local_qubits)
            self.assertEqual(row["contrast_exact_rank"], 2)
            self.assertAlmostEqual(row["contrast_trace_norm"], 0.2, places=12)
            self.assertAlmostEqual(row["witness_delta"], 0.2, places=12)

    def test_state_rank_separates_exponentially(self):
        rows = [synthetic_metrics(local_qubits) for local_qubits in range(3, 8)]
        self.assertTrue(all(rows[i + 1]["state_a_required_schmidt_rank"] > rows[i]["state_a_required_schmidt_rank"] for i in range(len(rows) - 1)))
        self.assertGreater(rows[-1]["state_to_contrast_rank_ratio"], 50.0)

    def test_tail_is_exact_trace_norm_residual(self):
        rng = np.random.default_rng(20260822)
        raw = rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8))
        matrix = 0.5 * (raw + raw.conj().T)
        approximation, info = truncate_hermitian_absolute(matrix, 3)
        self.assertAlmostEqual(
            trace_norm_hermitian(matrix - approximation),
            info["tail_trace_norm"],
            places=10,
        )

    def test_signed_basis_is_no_worse_than_state_averaged_for_same_rank(self):
        state_a, state_b = synthetic_pair(5)
        rho_a, rho_b = reduced_pair(state_a, state_b, 5)
        gamma = rho_b - rho_a
        signed, _ = truncate_hermitian_absolute(gamma, 2)
        averaged, _ = state_averaged_projection(gamma, 0.5 * (rho_a + rho_b), 2)
        self.assertLess(trace_norm_hermitian(gamma - signed), 1e-12)
        self.assertLessEqual(
            trace_norm_hermitian(gamma - signed),
            trace_norm_hermitian(gamma - averaged) + 1e-12,
        )

    def test_trace_norm_certifies_all_bounded_local_observables(self):
        rng = np.random.default_rng(7)
        raw = rng.normal(size=(12, 12)) + 1j * rng.normal(size=(12, 12))
        gamma = 0.5 * (raw + raw.conj().T)
        approximation, info = truncate_hermitian_absolute(gamma, 4)
        residual = gamma - approximation
        for _ in range(20):
            observable = rng.normal(size=(12, 12)) + 1j * rng.normal(size=(12, 12))
            observable = 0.5 * (observable + observable.conj().T)
            observable /= np.linalg.norm(observable, ord=2)
            error = abs(np.trace(observable @ residual))
            self.assertLessEqual(error, info["tail_trace_norm"] + 1e-10)


if __name__ == "__main__":
    unittest.main()
