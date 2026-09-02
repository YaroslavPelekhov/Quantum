from __future__ import annotations

import math
import unittest

import numpy as np

from .drift_models import (
    gate_visibility,
    odd_geometric_depths,
    rescaled_drift_path,
    target_probability,
    total_variation,
)
from .estimators import cosine_candidates, global_candidate_mle_estimate, sequential_unwrap_estimate
from .qae_core import (
    construct_visibility_confounding_witness,
    fit_power_law,
    known_visibility_fisher,
    per_round_efficient_fisher,
    physical_depth_budget,
    visibility_fisher_block,
)
from .run_phase0 import coherent_offset_audit


class DriftQAEPhase0Tests(unittest.TestCase):
    def test_odd_geometric_depths(self):
        self.assertEqual(odd_geometric_depths(6).tolist(), [1, 3, 7, 15, 31, 63])
        with self.assertRaises(ValueError):
            odd_geometric_depths(0)

    def test_drift_path_respects_bounds_and_variation(self):
        path = rescaled_drift_path(9, 0.78, 0.18, 0.55, 0.95, phase=0.31)
        self.assertGreaterEqual(float(np.min(path)), 0.55)
        self.assertLessEqual(float(np.max(path)), 0.95)
        self.assertLessEqual(total_variation(path), 0.18 + 1e-12)
        self.assertGreater(total_variation(path), 0.1)

    def test_exact_coherent_offset_no_go(self):
        audit = coherent_offset_audit(odd_geometric_depths(9))
        self.assertTrue(audit["exactly_indistinguishable"])
        self.assertGreater(audit["theta_separation"], 0.04)
        self.assertEqual(audit["offset_total_variation_first"], 0.0)
        self.assertEqual(audit["offset_total_variation_second"], 0.0)

    def test_constructed_visibility_witness_is_exact(self):
        depths = np.asarray([1, 3, 5])
        witness = construct_visibility_confounding_witness(
            0.04, 0.05, depths, (0.5, 1.0)
        )
        self.assertIsNotNone(witness)
        assert witness is not None
        self.assertLess(witness.maximum_probability_gap, 1e-14)
        self.assertLess(witness.total_variation_second, 0.1)

    def test_per_round_nuisance_has_zero_information_without_anchor(self):
        block = visibility_fisher_block(0.231, 31, 0.78, 128, 0)
        self.assertGreater(block.theta_theta, 0.0)
        self.assertAlmostEqual(block.efficient_theta, 0.0, places=8)
        anchored = visibility_fisher_block(0.231, 31, 0.78, 128, 128)
        self.assertGreater(anchored.efficient_theta, 0.0)
        self.assertLessEqual(anchored.efficient_theta, anchored.theta_theta)

    def test_depth_noise_fisher_upper_bound(self):
        gamma = 0.02
        theta = 0.231
        for depth in (1, 3, 7, 15, 31, 63, 127):
            visibility = gate_visibility(gamma, depth)
            information = known_visibility_fisher(
                theta,
                np.asarray([depth]),
                np.asarray([visibility]),
                1,
            )
            bound = 4.0 * depth**2 * math.exp(-2.0 * gamma * depth)
            self.assertLessEqual(information, bound + 1e-9)

    def test_physical_budget_charges_anchors(self):
        depths = odd_geometric_depths(4)
        self.assertEqual(physical_depth_budget(depths, 10, 0), 260)
        self.assertEqual(physical_depth_budget(depths, 10, 10), 520)

    def test_noiseless_unwrap_recovers_theta(self):
        theta = 0.231
        depths = odd_geometric_depths(6)
        shots = 1_000_000
        probabilities = target_probability(theta, depths, np.ones(len(depths)))
        successes = np.rint(shots * probabilities).astype(int)
        estimate, failed = sequential_unwrap_estimate(
            successes,
            shots,
            depths,
            np.ones(len(depths)),
            (0.08, 0.42),
        )
        self.assertFalse(failed)
        self.assertLess(abs(estimate - theta), 2e-6)

    def test_cosine_candidates_contain_true_branch(self):
        theta = 0.317
        depth = 31
        candidates = cosine_candidates(math.cos(2 * depth * theta), depth, (0.08, 0.42))
        self.assertLess(min(abs(value - theta) for value in candidates), 1e-12)

    def test_global_candidate_mle_resolves_noiseless_alias(self):
        theta = 0.317
        depths = odd_geometric_depths(8)
        shots = 2_000_000
        visibility = np.full(len(depths), 0.78)
        probabilities = target_probability(theta, depths, visibility)
        successes = np.rint(shots * probabilities).astype(int)
        estimate = global_candidate_mle_estimate(
            successes,
            shots,
            depths,
            visibility,
            (0.08, 0.42),
        )
        self.assertLess(abs(estimate - theta), 2e-6)

    def test_power_law_fit(self):
        budgets = np.asarray([10, 20, 40, 80, 160], dtype=float)
        errors = 3.0 * budgets ** -0.75
        fit = fit_power_law(budgets, errors)
        self.assertAlmostEqual(fit["slope"], -0.75, places=12)
        self.assertAlmostEqual(fit["r_squared"], 1.0, places=12)

    def test_schedule_information_is_additive(self):
        depths = odd_geometric_depths(5)
        visibility = np.full(len(depths), 0.78)
        total = per_round_efficient_fisher(0.231, depths, visibility, 128, 128)
        pieces = sum(
            visibility_fisher_block(0.231, int(depth), 0.78, 128, 128).efficient_theta
            for depth in depths
        )
        self.assertAlmostEqual(total, pieces, places=10)


if __name__ == "__main__":
    unittest.main()
