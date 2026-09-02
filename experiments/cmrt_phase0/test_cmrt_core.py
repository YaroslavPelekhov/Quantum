from __future__ import annotations

import math
import unittest

try:
    from .cmrt_core import (
        blocked_calibration_test_split,
        calibrate_heteroscedastic_conformal,
        certification_margins,
        finite_sample_quantile,
        finite_sample_quantile_level,
        heteroscedastic_nonconformity_scores,
        matched_coverage_metrics,
        rolling_blocked_splits,
        selective_metrics,
        sign_or_abstain,
        split_conformal_intervals,
        wilson_difference_interval,
        wilson_interval,
    )
except ImportError:
    from cmrt_core import (
        blocked_calibration_test_split,
        calibrate_heteroscedastic_conformal,
        certification_margins,
        finite_sample_quantile,
        finite_sample_quantile_level,
        heteroscedastic_nonconformity_scores,
        matched_coverage_metrics,
        rolling_blocked_splits,
        selective_metrics,
        sign_or_abstain,
        split_conformal_intervals,
        wilson_difference_interval,
        wilson_interval,
    )


class ConformalTests(unittest.TestCase):
    def test_registered_finite_sample_rank_and_higher_order_statistic(self):
        scores = tuple(range(1, 10))
        self.assertEqual(finite_sample_quantile_level(9, 0.2), 8 / 9)
        self.assertEqual(finite_sample_quantile(scores, 0.2), 8.0)

    def test_too_small_calibration_set_returns_infinite_radius(self):
        self.assertGreater(finite_sample_quantile_level(9, 0.05), 1.0)
        self.assertTrue(math.isinf(finite_sample_quantile(tuple(range(9)), 0.05)))

    def test_heteroscedastic_scores_and_fitted_metadata(self):
        scores = heteroscedastic_nonconformity_scores(
            [2.0, 1.0, -1.0, 8.0],
            [1.0, 2.0, -1.0, 4.0],
            [0.5, 2.0, 4.0, 2.0],
        )
        self.assertEqual(scores, (2.0, 0.5, 0.0, 2.0))
        fitted = calibrate_heteroscedastic_conformal(
            [2.0, 1.0, -1.0, 8.0],
            [1.0, 2.0, -1.0, 4.0],
            [0.5, 2.0, 4.0, 2.0],
            alpha=0.4,
        )
        self.assertEqual(fitted.n_calibration, 4)
        self.assertEqual(fitted.rank, 3)
        self.assertEqual(fitted.quantile_level, 0.75)
        self.assertEqual(fitted.qhat, 2.0)

    def test_intervals_scale_local_radius(self):
        lower, upper = split_conformal_intervals([10.0, -2.0], [0.5, 3.0], 2.0)
        self.assertEqual(lower, (9.0, -8.0))
        self.assertEqual(upper, (11.0, 4.0))

    def test_infinite_quantile_produces_vacuous_intervals(self):
        lower, upper = split_conformal_intervals([1.0], [2.0], math.inf)
        self.assertEqual(lower, (-math.inf,))
        self.assertEqual(upper, (math.inf,))

    def test_conformal_input_validation(self):
        bad_calls = (
            lambda: finite_sample_quantile([], 0.1),
            lambda: finite_sample_quantile([1.0, -0.1], 0.1),
            lambda: finite_sample_quantile([1.0], 0.0),
            lambda: finite_sample_quantile_level(0, 0.1),
            lambda: heteroscedastic_nonconformity_scores([1.0], [1.0, 2.0], [1.0]),
            lambda: heteroscedastic_nonconformity_scores([1.0], [1.0], [0.0]),
            lambda: split_conformal_intervals([1.0], [1.0, 2.0], 1.0),
            lambda: split_conformal_intervals([1.0], [1.0], -1.0),
        )
        for call in bad_calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


class CertificationTests(unittest.TestCase):
    def test_strict_sign_and_boundary_abstention(self):
        self.assertEqual(sign_or_abstain(0.1, 2.0), 1)
        self.assertEqual(sign_or_abstain(-2.0, -0.1), -1)
        self.assertEqual(sign_or_abstain(-1.0, 1.0), 0)
        self.assertEqual(sign_or_abstain(0.0, 1.0), 0)
        self.assertEqual(sign_or_abstain(-1.0, 0.0), 0)

    def test_nonzero_threshold_and_margins(self):
        self.assertEqual(sign_or_abstain(2.1, 3.0, threshold=2.0), 1)
        self.assertEqual(sign_or_abstain(1.0, 1.9, threshold=2.0), -1)
        self.assertEqual(
            certification_margins([2.1, 1.0, 1.5], [3.0, 1.9, 2.5], threshold=2.0),
            (0.10000000000000009, 0.10000000000000009, 0.0),
        )

    def test_bad_intervals_are_rejected(self):
        with self.assertRaises(ValueError):
            sign_or_abstain(2.0, 1.0)
        with self.assertRaises(ValueError):
            sign_or_abstain(math.nan, 1.0)
        with self.assertRaises(ValueError):
            certification_margins([0.0], [1.0, 2.0])


class IntervalTests(unittest.TestCase):
    def test_wilson_reference_value(self):
        interval = wilson_interval(5, 10)
        self.assertAlmostEqual(interval.lower, 0.2365930905, places=9)
        self.assertAlmostEqual(interval.upper, 0.7634069095, places=9)

    def test_wilson_handles_boundary_counts(self):
        zero = wilson_interval(0, 10)
        full = wilson_interval(10, 10)
        self.assertEqual(zero.lower, 0.0)
        self.assertAlmostEqual(zero.upper, 0.2775327999, places=9)
        self.assertAlmostEqual(full.lower, 1.0 - zero.upper, places=14)
        self.assertEqual(full.upper, 1.0)

    def test_newcombe_difference_contains_point_estimate(self):
        interval = wilson_difference_interval(8, 10, 4, 10)
        self.assertLessEqual(interval.lower, 0.4)
        self.assertGreaterEqual(interval.upper, 0.4)
        self.assertGreater(interval.lower, -1.0)
        self.assertLess(interval.upper, 1.0)

    def test_difference_is_antisymmetric_under_swap(self):
        ab = wilson_difference_interval(17, 23, 9, 19)
        ba = wilson_difference_interval(9, 19, 17, 23)
        self.assertAlmostEqual(ab.lower, -ba.upper, places=14)
        self.assertAlmostEqual(ab.upper, -ba.lower, places=14)

    def test_interval_count_validation(self):
        for call in (
            lambda: wilson_interval(-1, 10),
            lambda: wilson_interval(11, 10),
            lambda: wilson_interval(1, 0),
            lambda: wilson_interval(1.0, 10),
            lambda: wilson_difference_interval(1, 2, 3, 2),
        ):
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


class MatchedCoverageTests(unittest.TestCase):
    def test_selective_metrics_exclude_abstentions(self):
        result = selective_metrics([1, 0, -1, 1], [1, -1, 1, 1])
        self.assertEqual(result.n_total, 4)
        self.assertEqual(result.n_certified, 3)
        self.assertEqual(result.n_correct, 2)
        self.assertEqual(result.coverage, 0.75)
        self.assertAlmostEqual(result.selective_accuracy, 2 / 3)
        self.assertAlmostEqual(result.selective_risk, 1 / 3)

    def test_no_certifications_have_defined_coverage_not_accuracy(self):
        result = selective_metrics([0, 0], [1, -1])
        self.assertEqual(result.coverage, 0.0)
        self.assertIsNone(result.selective_accuracy)
        self.assertIsNone(result.selective_risk)

    def test_automatic_matching_uses_smaller_coverage(self):
        result = matched_coverage_metrics(
            [1, -1, 1, -1],
            [0.2, 0.9, 0.8, 0.1],
            [1, 0, -1, 0],
            [0.7, 0.0, 0.6, 0.0],
            [1, -1, 1, -1],
        )
        self.assertEqual(result.target_count, 2)
        self.assertEqual(result.target_coverage, 0.5)
        self.assertEqual(result.selected_indices_a, (1, 2))
        self.assertEqual(result.selected_indices_b, (0, 2))
        self.assertEqual(result.method_a.n_correct, 2)
        self.assertEqual(result.method_b.n_correct, 1)
        self.assertEqual(result.accuracy_difference, 0.5)
        self.assertIsNotNone(result.accuracy_difference_interval)

    def test_matching_ties_break_by_original_index(self):
        result = matched_coverage_metrics(
            [1, 1, 1],
            [0.5, 0.5, 0.5],
            [-1, -1, 0],
            [1.0, 1.0, 0.0],
            [1, 1, -1],
            target_count=1,
        )
        self.assertEqual(result.selected_indices_a, (0,))
        self.assertEqual(result.selected_indices_b, (0,))

    def test_zero_matched_coverage_is_explicit(self):
        result = matched_coverage_metrics(
            [0, 0], [0.0, 0.0], [1, 0], [0.2, 0.0], [1, -1]
        )
        self.assertEqual(result.target_count, 0)
        self.assertIsNone(result.accuracy_difference)
        self.assertIsNone(result.accuracy_difference_interval)

    def test_matching_never_uses_truth_for_selection(self):
        arguments = ([1, 1, 1], [0.2, 0.9, 0.4], [-1, -1, 0], [0.7, 0.6, 0.0])
        first = matched_coverage_metrics(*arguments, [1, 1, 1])
        second = matched_coverage_metrics(*arguments, [-1, -1, -1])
        self.assertEqual(first.selected_indices_a, second.selected_indices_a)
        self.assertEqual(first.selected_indices_b, second.selected_indices_b)


class BlockedSplitTests(unittest.TestCase):
    BLOCKS = ["day1", "day1", "day2", "day3", "day3", "day4", "day5"]

    def test_fraction_split_keeps_whole_blocks_and_gap(self):
        result = blocked_calibration_test_split(
            self.BLOCKS, calibration_fraction=0.4, gap_blocks=1
        )
        self.assertEqual(result.calibration_blocks, ("day1", "day2"))
        self.assertEqual(result.gap_blocks, ("day3",))
        self.assertEqual(result.test_blocks, ("day4", "day5"))
        self.assertEqual(result.calibration_indices, (0, 1, 2))
        self.assertEqual(result.gap_indices, (3, 4))
        self.assertEqual(result.test_indices, (5, 6))

    def test_exact_block_count(self):
        result = blocked_calibration_test_split(self.BLOCKS, calibration_blocks=3)
        self.assertEqual(result.calibration_indices, (0, 1, 2, 3, 4))
        self.assertEqual(result.gap_indices, ())
        self.assertEqual(result.test_indices, (5, 6))

    def test_reappearing_block_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contiguous"):
            blocked_calibration_test_split(["a", "b", "a"], calibration_blocks=1)

    def test_impossible_or_ambiguous_split_is_rejected(self):
        bad_calls = (
            lambda: blocked_calibration_test_split([], calibration_blocks=1),
            lambda: blocked_calibration_test_split(["a", "b"], calibration_blocks=1, gap_blocks=1),
            lambda: blocked_calibration_test_split(
                ["a", "b", "c"], calibration_fraction=0.5, calibration_blocks=1
            ),
            lambda: blocked_calibration_test_split(["a", "b"], calibration_fraction=0.1),
        )
        for call in bad_calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()

    def test_rolling_splits_are_forward_and_fixed_width(self):
        splits = rolling_blocked_splits(
            self.BLOCKS,
            calibration_blocks=2,
            gap_blocks=1,
            test_blocks=1,
            step_blocks=1,
        )
        self.assertEqual(len(splits), 2)
        self.assertEqual(splits[0].calibration_blocks, ("day1", "day2"))
        self.assertEqual(splits[0].gap_blocks, ("day3",))
        self.assertEqual(splits[0].test_blocks, ("day4",))
        self.assertEqual(splits[1].calibration_blocks, ("day2", "day3"))
        self.assertEqual(splits[1].gap_blocks, ("day4",))
        self.assertEqual(splits[1].test_blocks, ("day5",))

    def test_rolling_split_returns_empty_when_window_does_not_fit(self):
        self.assertEqual(
            rolling_blocked_splits(
                ["a", "b"], calibration_blocks=2, test_blocks=1
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
