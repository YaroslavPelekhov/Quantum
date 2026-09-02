from __future__ import annotations

import unittest

import networkx as nx
import numpy as np

from experiments.aquila_one_mask_phase0.control_core import (
    ControlLimits,
    addressability_capacity,
    full_c6_model,
    hard_blockade_model,
    max_local_detuning_area,
    phase_gauge_error,
    reflection_commutator_norm,
    validate_pulse,
)
from experiments.aquila_one_mask_phase0.lie_closure import control_generators, lie_dimension
from experiments.aquila_one_mask_phase0.pulse_opt import pulse_fidelity


class AquilaOneMaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coordinates = np.array([[0.0, 0.0], [5.5, 0.0], [11.0, 0.0], [16.5, 0.0]])
        cls.mask = np.linspace(0.0, 1.0, 4)
        cls.full = full_c6_model(cls.coordinates, cls.mask)
        cls.hard = hard_blockade_model(nx.path_graph(4), cls.coordinates, cls.mask)

    def test_dimensions_and_hermiticity(self):
        self.assertEqual(self.full.dimension, 16)
        self.assertEqual(self.hard.dimension, 8)
        hamiltonian = self.full.hamiltonian(2.0, 0.4, -3.0, -5.0)
        np.testing.assert_allclose(hamiltonian, hamiltonian.conj().T, atol=1e-12)

    def test_global_reflection_symmetry(self):
        self.assertLess(reflection_commutator_norm(self.full), 1e-12)

    def test_random_global_pulse_has_equal_reflected_probabilities(self):
        pulse = {
            "times_us": [0.0, 1.0, 2.0, 3.0, 4.0],
            "omega_rad_per_us": [0.0, 4.0, 7.0, 3.0, 0.0],
            "phase_rad": [0.0, 0.2, -0.5, 0.4, 0.0],
            "global_detuning_rad_per_us": [0.0, -20.0, 10.0, 30.0, 0.0],
            "local_detuning_rad_per_us": [0.0] * 5,
        }
        self.assertAlmostEqual(pulse_fidelity(self.full, pulse, 5), pulse_fidelity(self.full, pulse, 10), places=11)

    def test_uniform_mask_is_global_detuning(self):
        uniform = full_c6_model(self.coordinates, np.ones(4))
        first = uniform.hamiltonian(3.0, 0.2, 7.0, -4.0)
        second = uniform.hamiltonian(3.0, 0.2, 3.0, 0.0)
        np.testing.assert_allclose(first, second, atol=1e-12)

    def test_phase_gauge(self):
        self.assertLess(phase_gauge_error(), 1e-9)

    def test_action_formula(self):
        area = max_local_detuning_area(4.0, 125.0, 1256.0)
        self.assertAlmostEqual(area, 487.55971337579615)
        self.assertEqual(addressability_capacity(area), 173)

    def test_lie_rank_signal(self):
        self.assertEqual(lie_dimension(control_generators(self.hard, "gradient_mask"), 1e-9), 63)
        self.assertEqual(lie_dimension(control_generators(self.full, "gradient_mask"), 1e-9), 255)
        self.assertLess(lie_dimension(control_generators(self.full, "global_only"), 1e-9), 255)

    def test_pulse_validator(self):
        limits = ControlLimits()
        pulse = {
            "times_us": np.linspace(0.0, 4.0, 17).tolist(),
            "omega_rad_per_us": [0.0] * 17,
            "phase_rad": [0.0] * 17,
            "global_detuning_rad_per_us": [0.0] * 17,
            "local_detuning_rad_per_us": [0.0] * 17,
        }
        self.assertEqual(validate_pulse(pulse, limits), [])


if __name__ == "__main__":
    unittest.main()

