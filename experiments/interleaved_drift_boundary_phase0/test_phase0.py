from __future__ import annotations

import unittest

import numpy as np

from .core import (
    affine_drift,
    compact_bump_second_derivative,
    compact_bump_target_average,
    compact_target_bump,
    interval_average,
    physical_depth_cost,
    quadratic_drift,
    rtr_drift_averages,
    rtr_interpolation_bias,
)


class InterleavedDriftBoundaryTests(unittest.TestCase):
    def test_intervals_average_constant(self):
        averages = rtr_drift_averages(lambda _: 0.37, 5.0)
        self.assertTrue(all(abs(value - 0.37) < 1e-12 for value in averages))

    def test_affine_drift_cancels(self):
        for duration in (0.3, 1.0, 17.0):
            self.assertAlmostEqual(
                rtr_interpolation_bias(affine_drift(0.2, -0.07), duration),
                0.0,
                places=12,
            )

    def test_quadratic_saturates_half_kappa_t_squared(self):
        for duration in (0.3, 1.0, 17.0):
            curvature = 0.023
            bias = rtr_interpolation_bias(quadratic_drift(curvature), duration)
            self.assertAlmostEqual(bias, -0.5 * curvature * duration**2, places=11)

    def test_compact_bump_exact_average_and_support(self):
        curvature = 0.031
        duration = 2.7
        bump = compact_target_bump(curvature, duration)
        left, target, right = rtr_drift_averages(bump, duration)
        self.assertAlmostEqual(left, 0.0, places=14)
        self.assertAlmostEqual(right, 0.0, places=14)
        self.assertAlmostEqual(
            target,
            compact_bump_target_average(curvature, duration),
            places=12,
        )
        self.assertEqual(bump(-0.5 * duration), 0.0)
        self.assertEqual(bump(0.5 * duration), 0.0)

    def test_compact_bump_respects_curvature(self):
        curvature = 0.031
        duration = 2.7
        grid = np.linspace(-0.5 * duration, 0.5 * duration, 100_001)
        second = compact_bump_second_derivative(grid, curvature, duration)
        self.assertLessEqual(float(np.max(np.abs(second))), curvature * (1.0 + 1e-12))

    def test_interval_average_linear(self):
        self.assertAlmostEqual(interval_average(lambda time: 2.0 + 3.0 * time, (-1.0, 1.0)), 2.0)

    def test_physical_cost_charges_every_reference_and_quadrature(self):
        self.assertEqual(physical_depth_cost(31, 256), 6 * 31 * 256)


if __name__ == "__main__":
    unittest.main()

