from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from experiments.aquila_gauge_resource_phase0.full_dynamics_audit import (
    CLOCKWISE_TARGETS,
    COUNTERCLOCKWISE_TARGETS,
    FACE_SOURCES,
    FROZEN_PULSE,
    HARDWARE_QUANTIZED_POSITIONS_UM,
    build_model,
    copy_pulse,
    exact_unitary,
    native_ground_state_metrics,
    population_cycle_metrics,
    quantize_pulse,
    reverse_waveform,
    waveform_validation,
)


class FullDynamicsFalsificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pulse = copy_pulse(FROZEN_PULSE)
        cls.nominal_model = build_model()
        cls.nominal = exact_unitary(cls.nominal_model, cls.pulse)
        cls.reversed = exact_unitary(cls.nominal_model, reverse_waveform(cls.pulse))

    def test_frozen_waveform_satisfies_constraints(self):
        self.assertEqual(waveform_validation(self.pulse), [])
        quantized = quantize_pulse(self.pulse)
        self.assertEqual(waveform_validation(quantized), [])
        self.assertTrue(all(value == 0.0 for value in quantized["phase_rad"]))

    def test_adaptive_full_propagator_realizes_oriented_cycle(self):
        metrics = population_cycle_metrics(self.nominal)
        self.assertGreater(metrics["clockwise_mean"], 0.98)
        self.assertGreater(metrics["clockwise_minimum"], 0.97)
        self.assertLess(metrics["counterclockwise_mean"], 0.002)
        self.assertLess(metrics["spectator_leakage_mean"], 0.005)
        self.assertLess(metrics["unitarity_error_operator_norm"], 1e-9)
        self.assertEqual(FACE_SOURCES.tolist(), [0, 1, 3, 2])
        self.assertEqual(CLOCKWISE_TARGETS.tolist(), [1, 3, 2, 0])
        self.assertEqual(COUNTERCLOCKWISE_TARGETS.tolist(), [2, 0, 1, 3])

    def test_reversed_real_waveform_reverses_cycle(self):
        reversed_metrics = population_cycle_metrics(self.reversed)
        self.assertLess(reversed_metrics["clockwise_mean"], 0.002)
        self.assertGreater(reversed_metrics["counterclockwise_mean"], 0.98)
        self.assertLess(np.linalg.norm(self.reversed - self.nominal.T, ord=2), 1e-8)

    def test_interaction_off_is_reciprocal(self):
        no_interaction = replace(
            self.nominal_model,
            interaction=np.zeros_like(self.nominal_model.interaction),
        )
        metrics = population_cycle_metrics(exact_unitary(no_interaction, self.pulse))
        self.assertLess(abs(metrics["orientation_contrast"]), 1e-8)
        self.assertLess(metrics["clockwise_mean"], 0.3)

    def test_quantized_geometry_has_native_ground_state_signal(self):
        quantized = quantize_pulse(self.pulse)
        model = build_model(HARDWARE_QUANTIZED_POSITIONS_UM)
        forward = exact_unitary(model, quantized)
        reverse = exact_unitary(model, reverse_waveform(quantized))
        cycle = population_cycle_metrics(forward)
        native = native_ground_state_metrics(forward, reverse)
        self.assertGreater(cycle["clockwise_mean"], 0.98)
        self.assertGreater(cycle["clockwise_minimum"], 0.97)
        self.assertGreater(native["forward_target_site_0"], 0.97)
        self.assertGreater(native["reverse_target_site_1"], 0.98)
        self.assertLess(native["forward_wrong_site_1"], 0.002)
        self.assertLess(native["reverse_wrong_site_0"], 0.001)


if __name__ == "__main__":
    unittest.main()
