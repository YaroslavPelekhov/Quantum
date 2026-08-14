"""Implementation tests for the exact-calibrated MPS ladder."""

from __future__ import annotations

import unittest

import numpy as np
from qiskit.quantum_info import Statevector

import run_mps_ladder as ladder


class MPSLadderTests(unittest.TestCase):
    def test_frozen_settings_are_unique(self) -> None:
        self.assertEqual(len(ladder.SETTINGS), 11)
        self.assertEqual(len({row["name"] for row in ladder.SETTINGS}), 11)
        self.assertEqual(len(ladder.SETTINGS) * len(ladder.METHODS) * 2, 66)

    def test_small_mps_statevector_matches_exact(self) -> None:
        case = ladder.exact_extension.resource.prepare_case("karate", 4, "sorted")
        genome = np.asarray(ladder.METHODS["published_lr"])
        circuit = ladder.exact_extension.resource.circuit_for(case, genome, ladder.DEPTH)
        exact = np.asarray(Statevector.from_instruction(circuit.remove_final_measurements(False)))
        setting = {"name": "test", "family": "test", "bond": 64, "cutoff": 1e-12}
        result = ladder.mps_evaluate(case, genome, setting, exact)
        self.assertGreater(result["comparison"]["state_fidelity"], 1.0 - 1e-12)
        self.assertLess(result["comparison"]["total_variation_distance"], 1e-12)
        exact_metrics, _ = ladder.exact_extension.streaming_probability_metrics(case, exact)
        for metric in ladder.METRICS:
            self.assertAlmostEqual(result["metrics"][metric], exact_metrics[metric], places=12)

    def test_explicit_normalization_preserves_direction(self) -> None:
        state = np.asarray([1.0 + 1.0j, 2.0 - 1.0j], dtype=np.complex128)
        expected_direction = state / np.linalg.norm(state)
        raw_norm = ladder.normalize_state_in_place(state)
        self.assertAlmostEqual(raw_norm, 7.0, places=14)
        self.assertAlmostEqual(float(np.vdot(state, state).real), 1.0, places=14)
        np.testing.assert_allclose(state, expected_direction, rtol=0.0, atol=1e-15)


if __name__ == "__main__":
    unittest.main()
