from __future__ import annotations

import unittest

import numpy as np

from experiments.decision_conditioned_srdt.dcsrdt_core import (
    decision_conditioned_operator,
)
from .structural_core import frontier_profile, low_rank_spectrum, tensor_train_ranks


class StructuralAuditTests(unittest.TestCase):
    def test_low_rank_spectrum_matches_dense_operator(self):
        rng = np.random.default_rng(811)
        states = []
        for _ in range(2):
            state = rng.normal(size=64) + 1j * rng.normal(size=64)
            state /= np.linalg.norm(state)
            states.append(state)
        events = np.asarray([1, 7, 22, 39, 44], dtype=np.int64)
        effect = np.zeros(64)
        effect[events] = 1.0
        for cut in range(1, 6):
            dense = decision_conditioned_operator(
                states[0], states[1], effect, cut
            )
            expected = np.linalg.eigvalsh(dense)
            actual = low_rank_spectrum(states[0], states[1], events, cut)
            self.assertAlmostEqual(actual["trace"], float(expected.sum()), 12)
            self.assertAlmostEqual(
                actual["trace_norm"], float(np.abs(expected).sum()), 12
            )
            profile = frontier_profile(events, qubits=6)[cut - 1]
            self.assertLessEqual(
                actual["numerical_rank"], profile["structural_bound"]
            )

    def test_tighter_left_prefix_bound(self):
        events = np.asarray([0, 1, 2, 3, 8, 9], dtype=np.int64)
        profile = frontier_profile(events, qubits=5)[2]
        self.assertEqual(profile["s_left"], 2)
        self.assertEqual(profile["left_bound"], 4)
        self.assertEqual(profile["structural_bound"], 4)

    def test_paired_matching_can_tighten_prefix_count(self):
        # Three prefixes all connect to the same suffix.  Duplicating that
        # suffix permits a matching of size two, not three.
        events = np.asarray([0, 8, 16], dtype=np.int64)
        profile = frontier_profile(events, qubits=5)[2]
        self.assertEqual(profile["s_left"], 3)
        self.assertEqual(profile["s_right"], 1)
        self.assertEqual(profile["paired_matching_width"], 2)
        self.assertEqual(profile["structural_bound"], 4)

    def test_tensor_train_ranks_product_and_bell(self):
        product = np.ones(16, dtype=np.complex128) / 4.0
        self.assertEqual(tensor_train_ranks(product), [1, 1, 1])
        bell_product = np.zeros(16, dtype=np.complex128)
        bell_product[[0, 5, 10, 15]] = 0.5
        self.assertEqual(tensor_train_ranks(bell_product), [2, 4, 2])


if __name__ == "__main__":
    unittest.main()
