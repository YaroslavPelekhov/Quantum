from __future__ import annotations

import unittest
import json
import hashlib
from pathlib import Path

import numpy as np

from contrastive_core import (
    canonical_parameter_count,
    contrastive_operator_spectrum,
    density_to_operator_tensor,
    matched_contrast_bond,
    normalize_tt,
    operator_tensor_to_density,
    state_tt_metrics,
    tt_dense_inner,
    tt_evaluate_indices,
    tt_reconstruct,
    tt_svd_dense,
)
from sparse_tt_completion import (
    fit_tt_als,
    predict_indices,
    sample_distinct_indices,
)


class ContrastiveCoreTests(unittest.TestCase):
    def test_tt_exact_reconstruction_and_indexing(self):
        rng = np.random.default_rng(7)
        tensor = rng.normal(size=(2,) * 5) + 1j * rng.normal(size=(2,) * 5)
        cores, _ = tt_svd_dense(tensor, max_bond=16)
        reconstructed = tt_reconstruct(cores)
        self.assertLess(np.linalg.norm(tensor - reconstructed), 1e-11)
        indices = np.array([0, 1, 7, 16, 31])
        values = tt_evaluate_indices(cores, indices)
        np.testing.assert_allclose(values, tensor.reshape(-1)[indices], atol=1e-11)
        self.assertAlmostEqual(tt_dense_inner(tensor, cores), np.vdot(tensor, tensor), places=9)

    def test_state_metrics_exact_at_sufficient_bond(self):
        rng = np.random.default_rng(8)
        state = rng.normal(size=64) + 1j * rng.normal(size=64)
        state /= np.linalg.norm(state)
        metrics = state_tt_metrics(state, 6, [1, 5, 19], max_bond=8)
        self.assertAlmostEqual(metrics["fidelity"], 1.0, places=11)
        expected = float(np.square(np.abs(state[[1, 5, 19]])).sum())
        self.assertAlmostEqual(metrics["probability"], expected, places=11)

    def test_density_tensor_round_trip(self):
        rng = np.random.default_rng(9)
        matrix = rng.normal(size=(16, 16)) + 1j * rng.normal(size=(16, 16))
        tensor = density_to_operator_tensor(matrix, 4)
        restored = operator_tensor_to_density(tensor, 4)
        np.testing.assert_allclose(restored, matrix)

    def test_parameter_matching_never_exceeds_two_states(self):
        for sites in (7, 18, 24):
            for bond in (4, 8, 16, 32, 64):
                contrast = matched_contrast_bond(sites, bond)
                self.assertLessEqual(
                    canonical_parameter_count(sites, 2, contrast),
                    2 * canonical_parameter_count(sites, 2, bond),
                )
                if contrast < 2 ** (sites // 2):
                    self.assertGreater(
                        canonical_parameter_count(sites, 2, contrast + 1),
                        2 * canonical_parameter_count(sites, 2, bond),
                    )

    def test_identical_states_have_zero_difference_energy(self):
        rng = np.random.default_rng(10)
        state = rng.normal(size=32) + 1j * rng.normal(size=32)
        state /= np.linalg.norm(state)
        spectrum = contrastive_operator_spectrum(
            state, state, sites=5, cut=2, kind="difference", top=8
        )
        self.assertLess(abs(spectrum["total_frobenius_energy"]), 1e-12)
        self.assertLess(max(spectrum["leading_singular_values"], default=0.0), 1e-7)

    def test_operator_gram_spectrum_matches_explicit_reshuffle(self):
        rng = np.random.default_rng(11)
        state_a = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_b = rng.normal(size=16) + 1j * rng.normal(size=16)
        state_a /= np.linalg.norm(state_a)
        state_b /= np.linalg.norm(state_b)
        matrix_a = state_a.reshape(4, 4)
        matrix_b = state_b.reshape(4, 4)
        reshuffled_a = np.kron(matrix_a, matrix_a.conj())
        reshuffled_b = np.kron(matrix_b, matrix_b.conj())
        for kind, explicit in (
            ("mean", 0.5 * (reshuffled_a + reshuffled_b)),
            ("difference", 0.5 * (reshuffled_b - reshuffled_a)),
        ):
            expected = np.linalg.svd(explicit, compute_uv=False)
            actual = contrastive_operator_spectrum(
                state_a, state_b, sites=4, cut=2, kind=kind, top=16
            )["leading_singular_values"]
            np.testing.assert_allclose(actual, expected, atol=2e-8, rtol=2e-8)

    def test_completed_artifact_verdict_and_enclosures(self):
        repo = Path(__file__).resolve().parents[2]
        results = repo / "results" / "contrastive_tensor_simulation"
        summary_path = results / "summary.json"
        if not summary_path.exists():
            self.skipTest("Completed artifacts are not present")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        benchmark = json.loads(
            (results / "equal_budget_benchmark.json").read_text(encoding="utf-8")
        )
        self.assertFalse(summary["general_full_density_branch_survives"])
        self.assertTrue(summary["diagonal_contrast_branch_supported"])
        if "sparse_uniform_query_branch_supported" in summary:
            self.assertFalse(summary["sparse_uniform_query_branch_supported"])
        for row in benchmark["rows"]:
            self.assertLessEqual(
                row["contrast_parameter_budget"], row["separate_parameter_budget"]
            )
            self.assertLessEqual(
                abs(row["contrast_delta"] - row["exact_delta"]),
                row["contrast_certified_radius"] + 2e-10,
            )
            self.assertLessEqual(
                abs(row["separate_delta"] - row["exact_delta"]),
                row["separate_certified_radius"] + 2e-10,
            )
        sparse_path = results / "sparse_completion.json"
        if sparse_path.exists():
            sparse = json.loads(sparse_path.read_text(encoding="utf-8"))
            for row in sparse["rows"]:
                self.assertEqual(row["bks_training_overlap"], 0)
                self.assertEqual(row["bks_holdout_overlap"], 0)
                if row["case"] == "aves-sparrow-social":
                    self.assertLess(row["training_query_fraction"], 0.02)

    def test_completed_manifest_hashes(self):
        repo = Path(__file__).resolve().parents[2]
        path = repo / "results" / "contrastive_tensor_simulation" / "MANIFEST.json"
        if not path.exists():
            self.skipTest("Completed manifest is not present")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(manifest["complete"])
        for row in manifest["files"]:
            artifact = repo / row["path"]
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertEqual(digest, row["sha256"], row["path"])

    def test_sparse_als_recovers_synthetic_low_rank_tensor(self):
        rng = np.random.default_rng(12)
        sites = 8
        ranks = [1, 2, 2, 2, 2, 2, 2, 2, 1]
        cores = [
            rng.normal(size=(ranks[i], 2, ranks[i + 1]))
            for i in range(sites)
        ]
        all_indices = np.arange(2**sites, dtype=np.int64)
        bits = ((all_indices[:, None] >> np.arange(sites - 1, -1, -1)) & 1)
        values = np.ones((all_indices.size, 1))
        for site, core in enumerate(cores):
            selected = np.transpose(core[:, bits[:, site], :], (1, 0, 2))
            values = np.einsum("na,nab->nb", values, selected, optimize=True)
        training = sample_distinct_indices(2**sites, 180, set(), seed=13)
        fitted, _ = fit_tt_als(
            training,
            values[training, 0],
            sites=sites,
            max_rank=2,
            sweeps=10,
            relative_ridge=1e-12,
            seed=14,
        )
        prediction = predict_indices(fitted, all_indices, sites)
        relative = np.linalg.norm(prediction - values[:, 0]) / np.linalg.norm(values[:, 0])
        self.assertLess(relative, 1e-5)


if __name__ == "__main__":
    unittest.main()
