from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

import networkx as nx
import numpy as np

from experiments.dcsrdt_structural_audit.structural_core import low_rank_spectrum
from .quotient_core import (
    compile_twin_quotient,
    evolve_twin_quotient,
    quotient_decision_spectrum,
)

REPO = Path(__file__).resolve().parents[2]


class SymmetryDecisionRankTests(unittest.TestCase):
    def test_twin_quotient_matches_dense_state_and_decision_core(self):
        graph = nx.Graph([(0, 1), (1, 2), (2, 0), (0, 3)])
        order = list(range(4))
        indices = np.arange(16, dtype=np.uint32)
        selected = sum(((indices >> q) & 1) for q in range(4)).astype(np.int16)
        violations = sum(
            (((indices >> u) & 1) & ((indices >> v) & 1))
            for u, v in graph.edges()
        ).astype(np.int16)
        energy = selected - 2 * violations
        gammas = np.asarray([0.31, 0.57])
        beta_a = np.asarray([0.43, 0.19])
        beta_b = np.asarray([0.37, 0.23])

        def dense_state(betas):
            state = np.ones(16, dtype=np.complex128) / 4.0
            for gamma, beta in zip(gammas, betas, strict=True):
                state *= np.exp(-1j * gamma * energy)
                for qubit in range(4):
                    stride = 1 << qubit
                    view = state.reshape(-1, 2 * stride)
                    zero, one = view[:, :stride].copy(), view[:, stride:].copy()
                    view[:, :stride] = np.cos(beta) * zero - 1j * np.sin(beta) * one
                    view[:, stride:] = -1j * np.sin(beta) * zero + np.cos(beta) * one
            return state

        architecture = compile_twin_quotient(graph, order)
        quotient_a = evolve_twin_quotient(architecture, gammas, beta_a)
        quotient_b = evolve_twin_quotient(architecture, gammas, beta_b)
        dense_a, dense_b = dense_state(beta_a), dense_state(beta_b)
        self.assertLess(np.max(np.abs(quotient_a.dense() - dense_a)), 1e-12)
        self.assertLess(np.max(np.abs(quotient_b.dense() - dense_b)), 1e-12)
        events = np.asarray([2, 4, 10], dtype=np.int64)
        quotient = quotient_decision_spectrum(quotient_a, quotient_b, events, 2)
        dense = low_rank_spectrum(dense_a, dense_b, events, 2)
        self.assertEqual(quotient["numerical_rank"], dense["numerical_rank"])
        self.assertLess(abs(quotient["trace"] - dense["trace"]), 1e-12)
        self.assertLess(abs(quotient["trace_norm"] - dense["trace_norm"]), 1e-12)

    def test_manifest_hashes(self):
        manifest = json.loads(
            (REPO / "results" / "symmetry_quotient_decision_rank"
             / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["complete"])
        self.assertFalse(manifest["broad_ansatz_hypothesis_success"])
        for relative, expected in manifest["files"].items():
            actual = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_structural_and_coherence_audits(self):
        structural = json.loads(
            (REPO / "results" / "dcsrdt_structural_audit" / "audit.json")
            .read_text(encoding="utf-8")
        )
        coherence = json.loads(
            (REPO / "results" / "coherent_frontier_rank" / "coherence.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(structural["complete"])
        self.assertEqual(structural["summary"]["bound_violations"], 0)
        self.assertEqual(
            sum(
                cut["haar_numerical_rank"] == cut["structural_bound"]
                for row in structural["rows"] for cut in row["cuts"]
            ),
            104,
        )
        self.assertTrue(coherence["complete"])
        self.assertTrue(coherence["success"])
        self.assertEqual(
            coherence["summary"]["independent_phase_saturation_fraction"],
            1.0,
        )

    def test_broad_hypothesis_was_not_promoted(self):
        development = json.loads(
            (REPO / "results" / "ansatz_event_rank" / "development.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(development["complete"])
        self.assertFalse(development["success"])
        self.assertEqual(development["passed_rows"], 0)

    def test_symmetry_development_and_transfer(self):
        for stage, expected in (("development", 4), ("transfer", 2)):
            payload = json.loads(
                (REPO / "results" / "symmetry_quotient_decision_rank"
                 / f"{stage}.json").read_text(encoding="utf-8")
            )
            self.assertTrue(payload["complete"])
            self.assertTrue(payload["success"])
            self.assertEqual(payload["passed_rows"], expected)
            self.assertTrue(all(row["signatures_equal"] for row in payload["rows"]))
            self.assertTrue(all(row["phase_saturates"] for row in payload["rows"]))

    def test_real_24q_quotient_backend(self):
        payload = json.loads(
            (REPO / "results" / "symmetry_quotient_backend" / "backend.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(payload["complete"])
        self.assertTrue(payload["success"])
        self.assertFalse(payload["primary_path_loads_dense_state"])
        self.assertFalse(payload["primary_path_constructs_dense_operator"])
        self.assertEqual(payload["passed_rows"], 2)
        for row in payload["rows"]:
            self.assertGreaterEqual(row["dimension_compression"], 10.0)
            self.assertLess(max(row["sample_probability_errors"]), 1e-12)
            self.assertTrue(all(cut["rank_matches"] for cut in row["cuts"]))
        manifest = json.loads(
            (REPO / "results" / "symmetry_quotient_backend" / "manifest.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["backend_success"])
        for relative, expected in manifest["files"].items():
            self.assertEqual(
                hashlib.sha256((REPO / relative).read_bytes()).hexdigest(),
                expected,
                relative,
            )

    def test_preexisting_qoblib_breadth(self):
        payload = json.loads(
            (REPO / "results" / "symmetry_quotient_breadth" / "breadth.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(payload["selection_was_preexisting"])
        self.assertTrue(payload["success"])
        self.assertEqual(payload["passed_rows"], 7)
        self.assertEqual(len(payload["rows"]), 7)
        self.assertTrue(all(row["pass"] for row in payload["rows"]))
        manifest = json.loads(
            (REPO / "results" / "symmetry_quotient_breadth" / "manifest.json")
            .read_text(encoding="utf-8")
        )
        for relative, expected in manifest["files"].items():
            self.assertEqual(
                hashlib.sha256((REPO / relative).read_bytes()).hexdigest(),
                expected,
                relative,
            )


if __name__ == "__main__":
    unittest.main()
