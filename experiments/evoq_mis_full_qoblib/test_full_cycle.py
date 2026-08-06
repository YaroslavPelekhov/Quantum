import json
import unittest
from collections import defaultdict
from pathlib import Path

import numpy as np

import run_cycle as rc
from utils import qaoa_schedule


RESOURCE_RESULTS = Path(__file__).resolve().parent / "results" / "resource_aware"


class FullCycleTests(unittest.TestCase):
    def test_baseline_schedule_matches_published_linear_ramp(self):
        beta, gamma = rc.schedule(rc.BASELINE)
        expected_beta, expected_gamma = qaoa_schedule(0.7, 0.4, rc.P)
        np.testing.assert_allclose(beta, expected_beta)
        np.testing.assert_allclose(gamma, expected_gamma)

    def test_frozen_split_is_disjoint(self):
        names = set(rc.TRAIN_NAMES) | {rc.VALIDATION_NAME, rc.TEST_NAME}
        self.assertEqual(len(names), 4)
        self.assertNotIn(rc.TEST_NAME, rc.TRAIN_NAMES)

    def test_released_reduction_shape_is_reproduced(self):
        case = rc.prepare_case("es60fst02")
        self.assertEqual((case.original_vertices, case.original_edges), (186, 280))
        self.assertEqual((case.reduced_vertices, case.reduced_edges), (55, 91))
        self.assertFalse(case.decoder.repair_samples)

    def test_blind_artifact_is_complete_and_balanced(self):
        payload = json.loads((rc.RESULTS / "blind_test.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["complete"])
        rows = payload["rows"]
        self.assertEqual(len(rows), 45)
        for method in ("published_lr", "evolutionary_search", "matched_random_search"):
            selected = [row for row in rows if row["method"] == method]
            self.assertEqual(len(selected), 15)
            self.assertEqual(sum(row["metrics"]["total_shots"] for row in selected), 15000)

    def test_exact_calibration_is_complete_and_converged(self):
        payload = json.loads(
            (rc.RESULTS / "exact_mps_calibration.json").read_text(encoding="utf-8")
        )
        rows = payload["rows"]
        self.assertEqual(len(rows), 56)
        tight = [row for row in rows if row["threshold"] == 1e-6]
        self.assertEqual(len(tight), 4)
        for row in tight:
            self.assertGreater(row["distribution_errors"]["state_fidelity"], 0.9998)
            self.assertLess(abs(row["metric_errors"]["bks_rate"]), 2.3e-4)

    def test_exact_calibration_is_bond_invariant_above_16(self):
        payload = json.loads(
            (rc.RESULTS / "exact_mps_calibration.json").read_text(encoding="utf-8")
        )
        groups = defaultdict(list)
        for row in payload["rows"]:
            if row["bond"] >= 32 and row["threshold"] >= 1e-4:
                groups[(row["case"], row["method"], row["threshold"])].append(row)
        self.assertEqual(len(groups), 12)
        for rows in groups.values():
            self.assertEqual({row["bond"] for row in rows}, {32, 64, 128})
            reference = rows[0]
            for row in rows[1:]:
                self.assertAlmostEqual(
                    row["distribution_errors"]["total_variation"],
                    reference["distribution_errors"]["total_variation"],
                    places=12,
                )
                self.assertAlmostEqual(
                    row["metric_errors"]["bks_rate"],
                    reference["metric_errors"]["bks_rate"],
                    places=12,
                )

    def test_classical_baselines_are_complete_and_valid(self):
        payload = json.loads(
            (rc.RESULTS / "classical_baselines.json").read_text(encoding="utf-8")
        )
        exact = payload["exact"]
        self.assertTrue(exact["success"])
        self.assertEqual(exact["objective_size"], rc.BKS[rc.TEST_NAME])
        self.assertEqual(exact["mip_gap"], 0.0)
        case = rc.prepare_case(rc.TEST_NAME)
        selected = set(exact["selected_vertices"])
        self.assertTrue(
            all(u not in selected or v not in selected for u, v in case.graph.edges())
        )
        for key in ("full_graph_heuristic", "reduced_graph_heuristic"):
            summary = payload[key]["summary"]
            self.assertEqual(summary["total_runs"], 15_000)
            self.assertEqual(summary["feasible_rate"], 1.0)
            self.assertEqual(summary["best_size"], rc.BKS[rc.TEST_NAME])
        qaoa = json.loads((rc.RESULTS / "analysis_summary.json").read_text())["blind_summary"]
        best_qaoa = next(row for row in qaoa if row["method"] == "matched_random_search")
        self.assertGreater(
            payload["full_graph_heuristic"]["summary"]["bks_rate"],
            best_qaoa["bks_rate"],
        )

    def test_independent_cutensornet_audit_is_calibrated_and_complete(self):
        small = json.loads(
            (rc.RESULTS / "cutensornet" / "small_exact_validation.json").read_text()
        )
        self.assertEqual(len(small["rows"]), 8)
        for row in small["rows"]:
            self.assertGreater(row["state_fidelity"], 1 - 1e-10)
            self.assertLess(row["total_variation"], 1e-10)
        extended = json.loads((rc.RESULTS / "extended_comparison.json").read_text())
        comparisons = extended["cutensornet_5000shot_comparisons"]
        self.assertEqual(len(comparisons), 2)
        loose = next(row for row in comparisons if row["cutoff"] == 1e-3)
        tight = next(row for row in comparisons if row["cutoff"] == 1e-4)
        self.assertGreater(loose["nonlinear_bks_hits"], loose["lr_bks_hits"])
        self.assertLessEqual(
            abs(tight["nonlinear_bks_hits"] - tight["lr_bks_hits"]), 1
        )
        self.assertGreater(
            tight["nonlinear_feasible_rate"], tight["lr_feasible_rate"]
        )

    def test_resource_aware_preblind_protocol_is_complete(self):
        reachability = json.loads(
            (RESOURCE_RESULTS / "reachability.json").read_text(encoding="utf-8")
        )
        self.assertTrue(reachability["complete"])
        self.assertEqual(reachability["eligible_caps"], [4, 5, 6])
        self.assertEqual(reachability["selected_minimum_cap"], 4)
        blind_at_cap_three = next(
            row
            for row in reachability["rows"]
            if row["name"] == "es60fst02" and row["max_degree"] == 3
        )
        self.assertFalse(blind_at_cap_three["bks_reachable"])

        train = json.loads(
            (RESOURCE_RESULTS / "train_exact.json").read_text(encoding="utf-8")
        )
        self.assertTrue(train["complete"])
        self.assertEqual(train["configuration_count"], 210)
        self.assertEqual(train["training_eligible_count"], 53)
        self.assertEqual(len(train["rows"]), 210)

        screen = json.loads(
            (RESOURCE_RESULTS / "validation_screen.json").read_text(encoding="utf-8")
        )
        self.assertTrue(screen["complete"])
        ordering_errors = [
            error
            for row in screen["ordering_exact_check"]["rows"]
            for error in row["absolute_errors"].values()
        ]
        self.assertLess(max(ordering_errors), 1e-10)

    def test_resource_aware_confirmation_and_blind_are_complete(self):
        validation = json.loads(
            (RESOURCE_RESULTS / "validation_confirm.json").read_text(encoding="utf-8")
        )
        self.assertTrue(validation["complete"])
        self.assertEqual(len(validation["rows"]), 100)

        champion = json.loads(
            (RESOURCE_RESULTS / "frozen_resource_champion.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(champion["complete"])
        self.assertEqual(champion["status"], "no_eligible_resource_champion")
        self.assertIsNone(champion["config"])

        blind = json.loads(
            (RESOURCE_RESULTS / "blind_confirmation.json").read_text(encoding="utf-8")
        )
        self.assertTrue(blind["complete"])
        self.assertEqual(len(blind["rows"]), 60)
        cells = {
            (row["config_key"], row["setting"]): row["jobs"]
            for row in blind["summary"]
        }
        self.assertEqual(len(cells), 4)
        self.assertEqual(set(cells.values()), {15})
        self.assertEqual(sum(row["total_shots"] for row in blind["summary"]), 60_000)


if __name__ == "__main__":
    unittest.main()
