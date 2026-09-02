from __future__ import annotations

import unittest

import numpy as np

from experiments.aquila_gauge_resource_phase0.audit_theorem_constants import theorem_rows
from experiments.aquila_gauge_resource_phase0.gauge_core import (
    circular_gauge_cost,
    cube_complex,
    hashed_edge_phases,
    spectral_cost,
)


class GaugeResourcePhase0Tests(unittest.TestCase):
    def test_theorem_constant_audit(self):
        rows = theorem_rows()
        self.assertFalse(next(row for row in rows if row["n"] == 6)["existence_certified"])
        self.assertTrue(next(row for row in rows if row["n"] == 7)["existence_certified"])

    def test_cube_is_a_cochain_complex(self):
        for n in range(2, 6):
            complex_ = cube_complex(n)
            product = complex_.curl @ complex_.gradient
            self.assertEqual(product.nnz, 0)
            self.assertEqual(complex_.gradient.shape, (n * 2 ** (n - 1), 2**n))

    def test_hashed_targets_are_deterministic_and_distinct(self):
        edges = cube_complex(3).edges
        first = hashed_edge_phases("test", 3, 0, edges, 0.35)
        second = hashed_edge_phases("test", 3, 0, edges, 0.35)
        third = hashed_edge_phases("test", 3, 1, edges, 0.35)
        np.testing.assert_array_equal(first, second)
        self.assertFalse(np.array_equal(first, third))
        self.assertLessEqual(float(np.max(np.abs(first))), 0.35)

    def test_pure_gauge_has_zero_quotient_cost(self):
        complex_ = cube_complex(2)
        theta = np.array([0.0, 0.2, -0.4, 0.1])
        phases = np.asarray(complex_.gradient @ theta)
        frequencies = np.array([0.0, 0.21, 0.63, 1.0])
        result = circular_gauge_cost(phases, complex_.gradient, frequencies, time_limit_seconds=10)
        self.assertTrue(result["success"])
        self.assertLess(result["objective_upper"], 1e-8)

    def test_milp_preserves_flux_and_improves_raw_cost(self):
        complex_ = cube_complex(3)
        phases = hashed_edge_phases("unit", 3, 0, complex_.edges, 0.25)
        frequencies = np.linspace(0.0, 1.0, len(complex_.edges)) ** 1.3
        result = circular_gauge_cost(phases, complex_.gradient, frequencies, time_limit_seconds=20)
        self.assertTrue(result["success"])
        reference_flux = np.angle(np.exp(1j * (complex_.curl @ phases)))
        fitted_flux = np.angle(np.exp(1j * (complex_.curl @ result["representative"])))
        np.testing.assert_allclose(fitted_flux, reference_flux, atol=1e-8)
        order = result["order"]
        gaps = result["frequency_gaps"]
        self.assertLessEqual(
            spectral_cost(result["representative"], order, gaps),
            spectral_cost(phases, order, gaps) + 1e-8,
        )
        self.assertLess(result["constraint_error"], 1e-6)

    def test_one_square_spectral_order_constants(self):
        complex_ = cube_complex(2)
        signs = np.asarray(complex_.curl.toarray()[0])
        positive = np.flatnonzero(signs > 0).tolist()
        negative = np.flatnonzero(signs < 0).tolist()
        phases = np.zeros(len(complex_.edges))
        phases[positive[0]] = 0.4
        for order, expected in (
            (positive[:1] + negative[:1] + positive[1:] + negative[1:], 0.6),
            (positive + negative, 0.3),
        ):
            frequencies = np.empty(len(order))
            frequencies[order] = np.linspace(0.0, 1.0, len(order))
            result = circular_gauge_cost(
                phases, complex_.gradient, frequencies, time_limit_seconds=10
            )
            self.assertTrue(result["success"])
            self.assertAlmostEqual(result["objective_upper"], expected, places=8)


if __name__ == "__main__":
    unittest.main()
