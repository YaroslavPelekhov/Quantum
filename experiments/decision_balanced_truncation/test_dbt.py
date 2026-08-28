from __future__ import annotations

import unittest

import numpy as np
from qiskit.circuit.library import RXGate, RZZGate
from qiskit.quantum_info import Statevector

from .dbt_core import apply_gate_batch, balanced_projector, select_hankel_rank


class DecisionBalancedTests(unittest.TestCase):
    def test_batch_gate_matches_qiskit(self):
        rng = np.random.default_rng(20260823)
        states = rng.normal(size=(32, 3)) + 1j * rng.normal(size=(32, 3))
        states /= np.linalg.norm(states, axis=0)[None, :]
        for operation, qargs in ((RXGate(0.37), (3,)), (RZZGate(-0.81), (0, 4))):
            actual = apply_gate_batch(states, operation, qargs, 5)
            for column in range(states.shape[1]):
                expected = np.asarray(Statevector(states[:, column]).evolve(operation, qargs=list(qargs)).data)
                self.assertLess(np.linalg.norm(actual[:, column] - expected), 1e-12)

    def test_backward_batch_inverse(self):
        rng = np.random.default_rng(11)
        states = rng.normal(size=(16, 2)) + 1j * rng.normal(size=(16, 2))
        operation = RZZGate(0.42)
        forward = apply_gate_batch(states, operation, (1, 3), 4)
        backward = apply_gate_batch(forward, operation, (1, 3), 4, inverse=True)
        self.assertLess(np.linalg.norm(backward - states), 1e-12)

    def test_balanced_projector_is_biorthogonal(self):
        rng = np.random.default_rng(13)
        a = rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8))
        b = rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8))
        reachability = a @ a.conj().T
        observability = b @ b.conj().T
        projector, info = balanced_projector(reachability, observability, 3)
        self.assertFalse(info["fallback"])
        self.assertLess(info["biorthogonality_error"], 1e-10)
        self.assertLess(np.linalg.norm(projector @ projector - projector), 1e-9)

    def test_hankel_rank_selection(self):
        self.assertEqual(select_hankel_rank(np.array([1.0, 0.01, 0.001])), 1)
        self.assertEqual(select_hankel_rank(np.array([1.0, 1.0, 0.1])), 2)
        self.assertEqual(select_hankel_rank(np.ones(5)), 8)


if __name__ == "__main__":
    unittest.main()
