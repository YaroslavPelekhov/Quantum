from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from experiments.aquila_configuration_curvature_phase0.curvature_core import (
    analytic_weak_flux,
    branch_effective_hamiltonians,
    counts_witness,
    gauge_rephase,
    palindrome_pulse,
    plaquette_metrics,
    principal_effective,
    reverse_pulse,
    unitary_midpoint,
)
from experiments.aquila_one_mask_phase0.control_core import ControlLimits, full_c6_model, validate_pulse


ROOT = Path(__file__).resolve().parents[2]


class CurvaturePhase0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (ROOT / "experiments" / "aquila_configuration_curvature_phase0" / "protocol.json").read_text(
                encoding="utf-8"
            )
        )
        dev = cls.protocol["development_case"]
        cls.pulse = {
            key: list(dev[key])
            for key in (
                "times_us",
                "omega_rad_per_us",
                "phase_rad",
                "global_detuning_rad_per_us",
                "local_detuning_rad_per_us",
            )
        }
        cls.model = full_c6_model(
            np.array([[0.0, 0.0], [dev["distance_um"], 0.0]]), np.array(dev["mask"])
        )

    def test_pulse_is_provisionally_valid(self):
        limits = ControlLimits(duration_us=self.protocol["development_case"]["duration_us"])
        self.assertEqual(validate_pulse(self.pulse, limits), [])

    def test_reverse_transpose_identity(self):
        forward = unitary_midpoint(self.model, self.pulse, 16)
        reverse = unitary_midpoint(self.model, reverse_pulse(self.pulse), 16)
        np.testing.assert_allclose(reverse, forward.T, atol=2e-11)

    def test_palindrome_is_reciprocal(self):
        pulse = palindrome_pulse(self.pulse)
        forward = unitary_midpoint(self.model, pulse, 16)
        reverse = unitary_midpoint(self.model, reverse_pulse(pulse), 16)
        self.assertLess(abs(counts_witness(forward, reverse)["chi"]), 1e-11)

    def test_zero_interaction_is_reciprocal(self):
        model = replace(self.model, interaction=np.zeros_like(self.model.interaction))
        forward = unitary_midpoint(model, self.pulse, 16)
        reverse = unitary_midpoint(model, reverse_pulse(self.pulse), 16)
        self.assertLess(abs(counts_witness(forward, reverse)["chi"]), 1e-11)

    def test_principal_log_reconstructs(self):
        unitary = unitary_midpoint(self.model, self.pulse, 16)
        effective, diagnostic = principal_effective(unitary, 0.4)
        self.assertLess(diagnostic["reconstruction_error"], 1e-10)
        np.testing.assert_allclose(expm(-1j * 0.4 * effective), unitary, atol=1e-10)

    def test_wilson_product_is_gauge_invariant(self):
        unitary = unitary_midpoint(self.model, self.pulse, 16)
        effective, _ = principal_effective(unitary, 0.4)
        reference = plaquette_metrics(effective)["flux_rad"]
        transformed = gauge_rephase(effective, np.array([0.2, -0.7, 1.1, 2.0]))
        value = plaquette_metrics(transformed)["flux_rad"]
        self.assertLess(abs(np.angle(np.exp(1j * (value - reference)))), 1e-12)

    def test_branch_enumeration(self):
        unitary = unitary_midpoint(self.model, self.pulse, 8)
        rows = branch_effective_hamiltonians(unitary, 0.4)
        self.assertEqual(len(rows), 81)
        self.assertEqual(sum(row["common_shift_reduced"] for row in rows), 27)

    def test_analytic_weak_flux_packet(self):
        config = self.protocol["weak_drive_case"]
        mask = np.array(config["mask"])
        e1, e2 = -config["global_detuning_rad_per_us"] - config["local_detuning_rad_per_us"] * mask
        interaction = self.protocol["c6_rad_per_us_um6"] / config["distance_um"] ** 6
        flux = analytic_weak_flux(
            e1,
            e2,
            interaction,
            config["duration_us"],
            tuple(config["kick_centers_us"]),
            tuple(config["kick_peaks_rad_per_us"]),
        )
        self.assertAlmostEqual(flux, config["predicted_flux_rad"], places=5)


if __name__ == "__main__":
    unittest.main()

