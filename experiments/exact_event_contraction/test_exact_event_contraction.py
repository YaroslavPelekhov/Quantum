from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results" / "exact_event_contraction"
sys.path.insert(0, str(HERE))

from build_event_support import enumerate_maximum_independent_sets  # noqa: E402
from run_event_projector import (  # noqa: E402
    compile_indicator_tt,
    diagonal_mpo,
    evaluate_tt,
)


class ExactEventContractionTests(unittest.TestCase):
    def test_maximum_independent_set_enumerator(self) -> None:
        import networkx as nx

        graph = nx.cycle_graph(5)
        alpha, support = enumerate_maximum_independent_sets(graph)
        self.assertEqual(alpha, 2)
        self.assertEqual(len(support), 5)

    def test_frozen_55q_support(self) -> None:
        path = RESULTS / "event_support.json"
        if not path.exists():
            self.skipTest("event support has not been built")
        payload = json.loads(path.read_text(encoding="utf-8"))
        row = next(item for item in payload["cases"] if item["case"] == "es60fst02")
        self.assertEqual(row["qubits"], 55)
        self.assertEqual(row["edges"], 91)
        self.assertEqual(row["independence_number"], 23)
        self.assertEqual(row["support_size"], 384)
        self.assertEqual(row["decoded_sizes"], [88])
        for ordering in ("sorted", "spectral"):
            bitstrings = row["orderings"][ordering]["bitstrings_q0_first"]
            self.assertEqual(len(bitstrings), 384)
            self.assertEqual(len(set(bitstrings)), 384)
            self.assertTrue(all(len(value) == 55 for value in bitstrings))
            self.assertTrue(all(value.count("1") == 23 for value in bitstrings))

    def test_small_exact_self_test_when_present(self) -> None:
        path = RESULTS / "self_test_summary.json"
        if not path.exists():
            self.skipTest("cuTensorNet self-test has not been run")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["rows"]), 8)
        self.assertLessEqual(
            max(row["absolute_error"] for row in payload["rows"]), 1e-10
        )

    def test_exact_finite_event_tt(self) -> None:
        support = ["000", "011", "101"]
        cores = compile_indicator_tt(support)
        for value in (format(index, "03b") for index in range(8)):
            expected = 1.0 if value in support else 0.0
            self.assertAlmostEqual(evaluate_tt(cores, value).real, expected)
            self.assertAlmostEqual(evaluate_tt(cores, value).imag, 0.0)

    def test_diagonal_mpo_shapes(self) -> None:
        cores = compile_indicator_tt(["000", "111"])
        mpo = diagonal_mpo(cores)
        self.assertEqual(mpo[0].shape, (2, cores[0].shape[-1], 2))
        self.assertEqual(
            mpo[1].shape,
            (cores[1].shape[0], 2, cores[1].shape[-1], 2),
        )
        self.assertEqual(mpo[-1].shape, (cores[-1].shape[0], 2, 2))

    def test_frozen_mpo_audit_when_present(self) -> None:
        path = RESULTS / "mpo_representation_audit_summary.json"
        if not path.exists():
            self.skipTest("MPO representation audit has not been run")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["rows"]), 6)
        rows = {
            (row["case"], row["ordering"]): row for row in payload["rows"]
        }
        self.assertEqual(rows[("es60fst02", "sorted")]["max_bond_rank"], 152)
        self.assertEqual(rows[("es60fst02", "spectral")]["max_bond_rank"], 5)

    def test_lowlevel_mpo_self_test_when_present(self) -> None:
        path = RESULTS / "lowlevel_mpo_self_test_summary.json"
        if not path.exists():
            self.skipTest("low-level MPO self-test has not been run")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["rows"]), 8)
        self.assertLessEqual(payload["max_absolute_error"], 1e-10)

    def test_final_summary_when_present(self) -> None:
        path = RESULTS / "SUMMARY.json"
        if not path.exists():
            self.skipTest("final continuation summary has not been built")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["case"]["event_support_size"], 384)
        self.assertEqual(payload["projector"]["spectral"]["max_bond_rank"], 5)
        self.assertEqual(payload["largest_completed_55q_depth"], 2)
        self.assertFalse(
            payload["binding_verdict"]["depth_15_ranking_resolved"]
        )
        self.assertFalse(payload["binding_verdict"]["a_star_novelty_established"])
        for row in payload["completed_55q_depths"]:
            self.assertEqual(row["winner"], "matched_random_search")
            self.assertGreater(row["mr_minus_lr"], 0.0)
            self.assertLessEqual(
                row["published_lr"]["api_absolute_disagreement"], 1e-24
            )
            self.assertLessEqual(
                row["matched_random_search"]["api_absolute_disagreement"], 1e-24
            )

    def test_manifest_hashes_when_present(self) -> None:
        path = RESULTS / "MANIFEST.json"
        if not path.exists():
            self.skipTest("artifact manifest has not been built")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(payload["files"]), 100)
        for relative, expected in payload["files"].items():
            artifact = REPO / relative
            self.assertTrue(artifact.is_file(), relative)
            data = artifact.read_bytes()
            if artifact.suffix.lower() in {
                ".json",
                ".md",
                ".py",
                ".tex",
                ".txt",
            }:
                data = data.replace(b"\r\n", b"\n")
            actual = hashlib.sha256(data).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
