from __future__ import annotations

from pathlib import Path
import unittest

try:
    from .legacy_ibm_archive import (
        LegacyArchiveValidationError,
        default_repository_root,
        load_legacy_ibm_smoke_audit,
        raw_reduced_graph_feasible_shots,
    )
except ImportError:
    from legacy_ibm_archive import (
        LegacyArchiveValidationError,
        default_repository_root,
        load_legacy_ibm_smoke_audit,
        raw_reduced_graph_feasible_shots,
    )


class ReducedGraphFeasibilityTests(unittest.TestCase):
    def test_sorted_node_order_and_weighted_counts(self):
        counts = {
            "101": 4,  # sorted nodes (3, 7, 10): edge (3, 10) conflicts
            "011": 3,
            "100": 2,
        }
        self.assertEqual(
            raw_reduced_graph_feasible_shots(counts, [10, 3, 7], [(3, 10)]),
            5,
        )

    def test_invalid_bitstrings_and_edges_are_rejected(self):
        bad_calls = (
            lambda: raw_reduced_graph_feasible_shots({"00": 1}, [0], []),
            lambda: raw_reduced_graph_feasible_shots({"x": 1}, [0], []),
            lambda: raw_reduced_graph_feasible_shots({"0": 0}, [0], []),
            lambda: raw_reduced_graph_feasible_shots({"00": 1}, [0, 1], [(0, 2)]),
        )
        for call in bad_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()


class RealLegacyArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = default_repository_root()
        cls.audit = load_legacy_ibm_smoke_audit(cls.root)

    def test_repository_root_contains_the_archive_submodule(self):
        self.assertTrue((self.root / "baselines" / "qoblib-solutions").is_dir())

    def test_frozen_scope_metadata_forbids_inference_claims(self):
        metadata = self.audit.metadata
        self.assertEqual(metadata.audit_kind, "legacy_smoke_audit_only")
        self.assertEqual(metadata.job_blocks, 2)
        self.assertEqual(metadata.independent_instances, 1)
        self.assertEqual(metadata.independent_backends, 1)
        self.assertEqual(metadata.arms_per_job, 20)
        self.assertEqual(metadata.pairwise_comparisons_per_job, 190)
        self.assertTrue(metadata.not_independent_for_conformal)
        self.assertTrue(metadata.missing_transpiled_circuit_lineage)
        self.assertTrue(metadata.missing_calibration_lineage)
        self.assertFalse(metadata.allows_claim_or_generalization)

    def test_both_counts_sources_and_provenance_are_loaded(self):
        historical, current = self.audit.blocks
        self.assertEqual(historical.job_id, "d8k7s4r2d42s73c9smo0")
        self.assertEqual(historical.lambda_penalty, 1.0)
        self.assertEqual(historical.source_kind, "git_blob")
        self.assertEqual(historical.source_revision, "c8b29bd")
        self.assertIn("@c8b29bd:", historical.counts_locator)
        self.assertEqual(current.job_id, "d8l8g8rqv2lc73865vhg")
        self.assertEqual(current.lambda_penalty, 2.0)
        self.assertEqual(current.source_kind, "working_tree")
        self.assertIsNone(current.source_revision)
        self.assertTrue(Path(current.counts_locator).is_file())
        self.assertNotEqual(historical.counts_sha256, current.counts_sha256)

    def test_schema_sizes_and_shared_graph_are_frozen(self):
        graph_hashes = set()
        for block in self.audit.blocks:
            with self.subTest(job=block.job_id):
                self.assertEqual(block.instance, "es60fst02")
                self.assertEqual(block.backend_name, "ibm_boston")
                self.assertEqual(block.depth, 15)
                self.assertEqual(block.reduced_node_count, 55)
                self.assertEqual(block.reduced_edge_count, 91)
                self.assertEqual(block.total_shots, 20_000)
                self.assertEqual(len(block.arms), 20)
                self.assertEqual([arm.delta_index for arm in block.arms], list(range(20)))
                self.assertTrue(all(arm.total_shots == 1_000 for arm in block.arms))
                graph_hashes.add(block.graph_sha256)
        self.assertEqual(len(graph_hashes), 1)

    def test_per_arm_raw_feasibility_matches_the_archived_counts(self):
        historical, current = self.audit.blocks
        self.assertEqual(
            [arm.raw_feasible_shots for arm in historical.arms],
            [4, 6, 10, 12, 6, 7, 15, 13, 0, 4, 3, 6, 0, 0, 5, 6, 4, 0, 2, 2],
        )
        self.assertEqual(
            [arm.raw_feasible_shots for arm in current.arms],
            [12, 17, 11, 19, 2, 23, 23, 14, 6, 13, 17, 15, 8, 5, 10, 3, 5, 6, 5, 7],
        )
        self.assertEqual(historical.total_raw_feasible_shots, 105)
        self.assertEqual(current.total_raw_feasible_shots, 221)
        for block in self.audit.blocks:
            for arm in block.arms:
                self.assertEqual(
                    arm.raw_feasible_fraction,
                    arm.raw_feasible_shots / arm.total_shots,
                )

    def test_missing_repository_is_reported_without_creation(self):
        missing = self.root / "definitely_missing_cmrt_archive_root"
        self.assertFalse(missing.exists())
        with self.assertRaises(LegacyArchiveValidationError):
            load_legacy_ibm_smoke_audit(missing)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
