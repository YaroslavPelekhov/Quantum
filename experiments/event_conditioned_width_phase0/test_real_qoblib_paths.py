from __future__ import annotations

import itertools
import unittest

import numpy as np

from experiments.event_conditioned_width_phase0.run_real_qoblib_paths import (
    cardinality_factors,
    count_states,
)


def evaluate_counter(factors: list[np.ndarray], bits: tuple[int, ...]) -> complex:
    if len(factors) == 1:
        return complex(factors[0][bits[0]])
    value = factors[0][bits[0], :]
    for site in range(1, len(factors) - 1):
        value = value @ factors[site][:, bits[site], :]
    return complex(value @ factors[-1][:, bits[-1]])


class CardinalityFactorTests(unittest.TestCase):
    def test_exact_truth_table(self) -> None:
        for qubits in range(1, 8):
            for target in range(qubits + 1):
                factors = cardinality_factors(qubits, target)
                for bits in itertools.product((0, 1), repeat=qubits):
                    expected = float(sum(bits) == target)
                    self.assertEqual(evaluate_counter(factors, bits), expected)

    def test_every_counter_state_is_reachable_and_completable(self) -> None:
        for qubits in range(2, 10):
            for target in range(qubits + 1):
                for cut in range(qubits + 1):
                    for count in count_states(qubits, target, cut):
                        self.assertLessEqual(count, cut)
                        self.assertLessEqual(target - count, qubits - cut)


if __name__ == "__main__":
    unittest.main()
