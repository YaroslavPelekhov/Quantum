from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .gdbc_core import balanced_factors, global_reduced_contraction


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "global_decision_balanced_contraction"


class GlobalDecisionBalancedTests(unittest.TestCase):
    def test_balanced_factors_are_biorthogonal(self):
        rng = np.random.default_rng(31)
        a = rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8))
        b = rng.normal(size=(8, 8)) + 1j * rng.normal(size=(8, 8))
        trial, test, info = balanced_factors(a @ a.conj().T, b @ b.conj().T, 4)
        self.assertFalse(info["fallback"])
        self.assertLess(np.linalg.norm(test.conj().T @ trial - np.eye(4)), 1e-10)

    def test_full_rank_global_recurrence_is_exact(self):
        circuit_a = QuantumCircuit(3)
        circuit_a.h(0)
        circuit_a.rzz(0.3, 0, 2)
        circuit_a.rx(-0.7, 1)
        circuit_b = QuantumCircuit(3)
        circuit_b.h(0)
        circuit_b.rzz(-0.2, 0, 2)
        circuit_b.rx(0.4, 1)
        identity = np.eye(2, dtype=np.complex128)
        bases = [(identity, identity) for _ in circuit_a.data]
        actual = global_reduced_contraction(circuit_a, circuit_b, bases, cut=1)
        expected_a = np.asarray(Statevector.from_instruction(circuit_a).data)
        expected_b = np.asarray(Statevector.from_instruction(circuit_b).data)
        self.assertLess(np.linalg.norm(actual[:, 0] - expected_a), 1e-12)
        self.assertLess(np.linalg.norm(actual[:, 1] - expected_b), 1e-12)

    def test_frozen_development_failure_blocks_transfer(self):
        development = json.loads(
            (RESULTS / "development.json").read_text(encoding="utf-8")
        )
        self.assertTrue(development["complete"])
        self.assertFalse(development["success"])
        self.assertEqual(development["passed_rows"], 2)
        self.assertFalse((RESULTS / "transfer.json").exists())

    def test_manifest_hashes(self):
        manifest = json.loads(
            (RESULTS / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["development_success"])
        self.assertFalse(manifest["transfer_promoted"])
        for relative, expected in manifest["files"].items():
            actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
