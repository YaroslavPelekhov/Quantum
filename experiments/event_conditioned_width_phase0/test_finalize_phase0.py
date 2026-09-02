"""Regression tests for the frozen Phase-0 decision summary."""

from __future__ import annotations

import unittest

from experiments.event_conditioned_width_phase0.finalize_phase0 import build_decision


class FinalizePhase0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.decision = build_decision()

    def test_k6_scope_is_binding_but_does_not_claim_actual_qaoa_width(self) -> None:
        self.assertEqual(self.decision["final_verdict"], "INCOMPLETE_NO_PROMOTION")
        natural = self.decision["subclaim_verdicts"][
            "natural_product_proxy_as_new_width"
        ]
        self.assertEqual(natural["verdict"], "KILLED_AS_ASTAR_SOURCE")
        self.assertEqual(natural["kill_gate"], "K6")
        limits = self.decision["scope_limits"]
        self.assertFalse(limits["actual_qaoa_circuit_width_theorem_established"])
        self.assertFalse(limits["broader_algebraic_pair_dependent_algorithm_killed"])
        self.assertEqual(limits["qpu_jobs_submitted"], 0)

    def test_structural_and_development_counts_are_complete(self) -> None:
        evidence = self.decision["evidence"]
        structural = evidence["structural"]
        self.assertEqual(structural["rows"], 48)
        self.assertEqual(structural["independently_evaluated_permutations"], 3_272_832)
        self.assertEqual(structural["optimizer_evaluated_permutations"], 9_818_496)
        self.assertEqual(structural["strict_joint_headroom_rows"], 0)
        self.assertEqual(structural["tie_aware_headroom_min"], 1.0)
        self.assertEqual(structural["tie_aware_headroom_max"], 1.0)
        development = evidence["development_representation"]
        self.assertEqual(development["cases"], 48)
        self.assertEqual(development["support_mpo_flop_wins"], 48)

    def test_real_screen_retains_the_order_reversal_without_overreading_it(self) -> None:
        real = self.decision["evidence"]["real_path_sentinel"]
        self.assertEqual(real["rows"], 12)
        indexed = {
            (row["ordering"], row["depth"]): row
            for row in real["paired_comparisons"]
        }
        self.assertEqual(indexed[("spectral", 2)]["winner"], "minimal_mpo")
        self.assertEqual(indexed[("sorted", 2)]["winner"], "local_mis")
        self.assertTrue(
            all(
                row["best_local_over_best_mpo_opt_cost"] > 1.0
                for row in real["best_tested_order_by_depth"]
            )
        )


if __name__ == "__main__":
    unittest.main()
