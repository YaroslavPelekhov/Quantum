from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from experiments.decision_conditioned_srdt.dcsrdt_core import (
    decision_conditioned_operator,
)
from .sparse_mps_core import (
    decision_operator_from_mps_pair,
    enumerate_bks_support,
    mps_amplitude,
    mps_norm,
    spectral_summary,
)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "sparse_mps_dcsrdt"


def exact_mps(circuit):
    executable = circuit.copy()
    executable.save_matrix_product_state()
    return AerSimulator(method="matrix_product_state").run(executable).result().data(0)[
        "matrix_product_state"
    ]


class SparseMPSDCSRTTests(unittest.TestCase):
    def test_amplitudes_and_norm_match_statevector(self):
        circuit = QuantumCircuit(4)
        circuit.h(0)
        circuit.ry(0.31, 2)
        circuit.cx(0, 3)
        circuit.rzz(-0.27, 1, 2)
        mps = exact_mps(circuit)
        expected = np.asarray(Statevector.from_instruction(circuit).data)
        actual = np.asarray([mps_amplitude(mps, index) for index in range(16)])
        self.assertLess(np.linalg.norm(actual - expected), 1e-12)
        self.assertAlmostEqual(mps_norm(mps), 1.0)

    def test_sparse_support_matches_bruteforce(self):
        scorer = {
            "constant_selected": 0,
            "weights": [1, 1, 1, 1],
            "forbidden": [[3, 3], [12, 12]],
            "impossible": False,
            "bks": 2,
        }
        expected = []
        for index in range(16):
            feasible = all((index & mask) != pattern for mask, pattern in scorer["forbidden"])
            if feasible and index.bit_count() >= 2:
                expected.append(index)
        self.assertEqual(enumerate_bks_support(scorer), expected)

    def test_direct_operator_matches_dense(self):
        circuit_a = QuantumCircuit(5)
        circuit_a.h(0)
        circuit_a.ry(0.4, 3)
        circuit_a.cx(0, 4)
        circuit_a.rzz(0.2, 1, 3)
        circuit_b = QuantumCircuit(5)
        circuit_b.h(0)
        circuit_b.ry(-0.3, 3)
        circuit_b.cx(0, 4)
        circuit_b.rzz(-0.5, 1, 3)
        support = [3, 7, 19, 23]
        direct, _ = decision_operator_from_mps_pair(
            exact_mps(circuit_a), exact_mps(circuit_b), support, cut=2
        )
        state_a = np.asarray(Statevector.from_instruction(circuit_a).data)
        state_b = np.asarray(Statevector.from_instruction(circuit_b).data)
        effect = np.zeros(32)
        effect[support] = 1.0
        dense = decision_conditioned_operator(state_a, state_b, effect, cut=2)
        self.assertLess(np.linalg.norm(direct - dense), 1e-12)

    def test_spectral_tail_bounds_trace_error(self):
        operator = np.diag([0.4, -0.3, 0.2, -0.1])
        summary = spectral_summary(operator, 2)
        self.assertAlmostEqual(summary["tail_trace_norm"], 0.3)
        self.assertLessEqual(
            abs(summary["estimate"] - np.trace(operator).real),
            summary["tail_trace_norm"],
        )

    def test_frozen_failure_blocks_transfer(self):
        development = json.loads(
            (RESULTS / "development.json").read_text(encoding="utf-8")
        )
        self.assertFalse(development["success"])
        self.assertEqual(development["passed_rows"], 0)
        self.assertFalse((RESULTS / "transfer.json").exists())

    def test_manifest_hashes(self):
        manifest = json.loads(
            (RESULTS / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["development_success"])
        self.assertFalse(manifest["transfer_promoted"])
        self.assertFalse(manifest["calibrated_replication_success"])
        self.assertTrue(manifest["same_mps_identity_validated"])
        for relative, expected in manifest["files"].items():
            actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_calibrated_replication_and_snapshot_semantics(self):
        replication = json.loads(
            (RESULTS / "calibrated_replication.json").read_text(encoding="utf-8")
        )
        semantics = json.loads(
            (RESULTS / "snapshot_semantics.json").read_text(encoding="utf-8")
        )
        self.assertFalse(replication["success"])
        self.assertEqual(replication["passed_rows"], 0)
        self.assertLess(
            max(
                row["fresh_vs_archive_error"]
                for row in semantics["rows"].values()
            ),
            2e-15,
        )
        self.assertGreater(semantics["gap_difference"], 1e-3)


if __name__ == "__main__":
    unittest.main()
