"""Deterministic statistical core for CMRT Phase 0.

The module deliberately has no simulator or machine-learning dependencies.  It
contains only the pieces whose semantics must stay frozen across experiments:

* finite-sample split-conformal calibration with heteroscedastic scales;
* interval-to-sign certification with an explicit abstention state;
* Wilson intervals, including the Newcombe interval for a difference;
* equal-coverage comparison of two selective rules; and
* leakage-resistant splits which keep complete ordered blocks together.

All tie breaks are by original example index, so repeated runs are bitwise
deterministic for identical Python inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import NormalDist
from typing import Hashable, Iterable, Sequence


@dataclass(frozen=True)
class ConformalCalibration:
    """A fitted split-conformal multiplier and its finite-sample rank."""

    alpha: float
    n_calibration: int
    rank: int
    quantile_level: float
    qhat: float


@dataclass(frozen=True)
class ProportionInterval:
    """A closed confidence interval with its nominal confidence level."""

    lower: float
    upper: float
    confidence: float


@dataclass(frozen=True)
class SelectiveMetrics:
    """Coverage and accuracy of a rule whose decision 0 means abstain."""

    n_total: int
    n_certified: int
    n_correct: int
    coverage: float
    selective_accuracy: float | None
    selective_risk: float | None


@dataclass(frozen=True)
class MatchedCoverageMetrics:
    """Comparison after independently retaining the same number of decisions."""

    target_count: int
    target_coverage: float
    method_a: SelectiveMetrics
    method_b: SelectiveMetrics
    selected_indices_a: tuple[int, ...]
    selected_indices_b: tuple[int, ...]
    accuracy_difference: float | None
    accuracy_difference_interval: ProportionInterval | None


@dataclass(frozen=True)
class BlockedSplit:
    """Indices in calibration, embargo/gap, and test partitions."""

    calibration_indices: tuple[int, ...]
    gap_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    calibration_blocks: tuple[Hashable, ...]
    gap_blocks: tuple[Hashable, ...]
    test_blocks: tuple[Hashable, ...]


def _validate_alpha(alpha: float, *, name: str = "alpha") -> float:
    value = float(alpha)
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be finite and strictly between 0 and 1")
    return value


def _finite_floats(values: Iterable[float], *, name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError(f"{name} must be non-empty")
    if any(not math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain only finite values")
    return result


def finite_sample_quantile_level(n_calibration: int, alpha: float) -> float:
    """Return ``ceil((n + 1) * (1 - alpha)) / n`` exactly as registered.

    The result can exceed one when the calibration set is too small for the
    requested miscoverage.  In that case :func:`finite_sample_quantile`
    returns ``+inf`` rather than silently clipping the rank and overstating a
    coverage guarantee.
    """

    if isinstance(n_calibration, bool) or not isinstance(n_calibration, int):
        raise TypeError("n_calibration must be an integer")
    if n_calibration <= 0:
        raise ValueError("n_calibration must be positive")
    alpha = _validate_alpha(alpha)
    rank = math.ceil((n_calibration + 1) * (1.0 - alpha))
    return rank / n_calibration


def finite_sample_quantile(scores: Sequence[float], alpha: float) -> float:
    """Return the conservative finite-sample split-conformal quantile.

    Sorting and selecting the one-indexed rank is equivalent to the empirical
    ``higher`` quantile at :func:`finite_sample_quantile_level`.  If that rank
    is ``n + 1``, the conformal order statistic includes a point at infinity;
    this function therefore returns ``+inf``.
    """

    clean = _finite_floats(scores, name="scores")
    if any(score < 0.0 for score in clean):
        raise ValueError("scores must be non-negative")
    alpha = _validate_alpha(alpha)
    rank = math.ceil((len(clean) + 1) * (1.0 - alpha))
    if rank > len(clean):
        return math.inf
    return sorted(clean)[rank - 1]


def heteroscedastic_nonconformity_scores(
    observed: Sequence[float],
    predicted: Sequence[float],
    scales: Sequence[float],
) -> tuple[float, ...]:
    """Compute ``abs(observed - predicted) / scale`` for calibration rows."""

    y = _finite_floats(observed, name="observed")
    yhat = _finite_floats(predicted, name="predicted")
    sigma = _finite_floats(scales, name="scales")
    if not (len(y) == len(yhat) == len(sigma)):
        raise ValueError("observed, predicted, and scales must have equal length")
    if any(scale <= 0.0 for scale in sigma):
        raise ValueError("all heteroscedastic scales must be strictly positive")
    return tuple(abs(actual - estimate) / scale for actual, estimate, scale in zip(y, yhat, sigma))


def calibrate_heteroscedastic_conformal(
    observed: Sequence[float],
    predicted: Sequence[float],
    scales: Sequence[float],
    *,
    alpha: float,
) -> ConformalCalibration:
    """Fit the scalar multiplier used by heteroscedastic split conformal."""

    alpha = _validate_alpha(alpha)
    scores = heteroscedastic_nonconformity_scores(observed, predicted, scales)
    n = len(scores)
    rank = math.ceil((n + 1) * (1.0 - alpha))
    return ConformalCalibration(
        alpha=alpha,
        n_calibration=n,
        rank=rank,
        quantile_level=rank / n,
        qhat=finite_sample_quantile(scores, alpha),
    )


def split_conformal_intervals(
    predicted: Sequence[float],
    scales: Sequence[float],
    calibration: ConformalCalibration | float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Apply a calibrated heteroscedastic interval ``prediction +/- qhat*scale``."""

    yhat = _finite_floats(predicted, name="predicted")
    sigma = _finite_floats(scales, name="scales")
    if len(yhat) != len(sigma):
        raise ValueError("predicted and scales must have equal length")
    if any(scale <= 0.0 for scale in sigma):
        raise ValueError("all heteroscedastic scales must be strictly positive")
    qhat = calibration.qhat if isinstance(calibration, ConformalCalibration) else float(calibration)
    if math.isnan(qhat) or qhat < 0.0:
        raise ValueError("qhat must be non-negative and not NaN")
    radii = tuple(qhat * scale for scale in sigma)
    lower = tuple(center - radius for center, radius in zip(yhat, radii))
    upper = tuple(center + radius for center, radius in zip(yhat, radii))
    return lower, upper


def _validate_interval(lower: float, upper: float) -> tuple[float, float]:
    lower = float(lower)
    upper = float(upper)
    if math.isnan(lower) or math.isnan(upper):
        raise ValueError("interval endpoints must not be NaN")
    if lower > upper:
        raise ValueError("interval lower endpoint must not exceed upper endpoint")
    return lower, upper


def sign_or_abstain(lower: float, upper: float, *, threshold: float = 0.0) -> int:
    """Certify -1 or +1 only when the closed interval excludes ``threshold``.

    Touching the threshold is deliberately an abstention, so the return value
    is always one of ``-1, 0, +1``.
    """

    lower, upper = _validate_interval(lower, upper)
    threshold = float(threshold)
    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite")
    if lower > threshold:
        return 1
    if upper < threshold:
        return -1
    return 0


def certification_margins(
    lower: Sequence[float],
    upper: Sequence[float],
    *,
    threshold: float = 0.0,
) -> tuple[float, ...]:
    """Return distance from threshold for certified intervals, else zero."""

    if len(lower) != len(upper):
        raise ValueError("lower and upper must have equal length")
    threshold = float(threshold)
    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite")
    margins: list[float] = []
    for raw_lower, raw_upper in zip(lower, upper):
        lo, hi = _validate_interval(raw_lower, raw_upper)
        if lo > threshold:
            margins.append(lo - threshold)
        elif hi < threshold:
            margins.append(threshold - hi)
        else:
            margins.append(0.0)
    return tuple(margins)


def wilson_interval(
    successes: int,
    total: int,
    *,
    confidence: float = 0.95,
) -> ProportionInterval:
    """Two-sided Wilson score interval for one binomial proportion."""

    if isinstance(successes, bool) or isinstance(total, bool):
        raise TypeError("successes and total must be integers")
    if not isinstance(successes, int) or not isinstance(total, int):
        raise TypeError("successes and total must be integers")
    if total <= 0:
        raise ValueError("total must be positive")
    if not 0 <= successes <= total:
        raise ValueError("successes must lie between zero and total")
    confidence = _validate_alpha(confidence, name="confidence")
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    z2 = z * z
    phat = successes / total
    denominator = 1.0 + z2 / total
    center = (phat + z2 / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt(phat * (1.0 - phat) / total + z2 / (4.0 * total * total))
        / denominator
    )
    return ProportionInterval(
        # Preserve the exact analytical boundary values instead of exposing a
        # platform-dependent floating-point epsilon at 0/total or total/total.
        lower=0.0 if successes == 0 else max(0.0, center - half_width),
        upper=1.0 if successes == total else min(1.0, center + half_width),
        confidence=confidence,
    )


def wilson_difference_interval(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
    *,
    confidence: float = 0.95,
) -> ProportionInterval:
    """Newcombe-Wilson interval for ``p_a - p_b`` (independent samples).

    This is Newcombe's score-based construction without continuity correction,
    not a paired/McNemar interval.  It is appropriate for independently chosen
    equal-coverage cohorts and is exposed explicitly so downstream reports do
    not substitute a Wald interval.
    """

    interval_a = wilson_interval(successes_a, total_a, confidence=confidence)
    interval_b = wilson_interval(successes_b, total_b, confidence=confidence)
    phat_a = successes_a / total_a
    phat_b = successes_b / total_b
    difference = phat_a - phat_b
    lower_offset = math.sqrt(
        (phat_a - interval_a.lower) ** 2 + (interval_b.upper - phat_b) ** 2
    )
    upper_offset = math.sqrt(
        (interval_a.upper - phat_a) ** 2 + (phat_b - interval_b.lower) ** 2
    )
    return ProportionInterval(
        lower=max(-1.0, difference - lower_offset),
        upper=min(1.0, difference + upper_offset),
        confidence=float(confidence),
    )


def _validated_decisions(values: Sequence[int], *, name: str) -> tuple[int, ...]:
    result = tuple(values)
    if any(isinstance(value, bool) or value not in (-1, 0, 1) for value in result):
        raise ValueError(f"{name} values must be -1, 0, or +1")
    return result


def _validated_truth(values: Sequence[int]) -> tuple[int, ...]:
    result = tuple(values)
    if any(isinstance(value, bool) or value not in (-1, 1) for value in result):
        raise ValueError("truth values must be -1 or +1")
    return result


def selective_metrics(decisions: Sequence[int], truth: Sequence[int]) -> SelectiveMetrics:
    """Compute coverage and conditional accuracy without scoring abstentions."""

    predicted = _validated_decisions(decisions, name="decisions")
    actual = _validated_truth(truth)
    if len(predicted) != len(actual):
        raise ValueError("decisions and truth must have equal length")
    if not actual:
        raise ValueError("decisions and truth must be non-empty")
    certified = [index for index, decision in enumerate(predicted) if decision != 0]
    correct = sum(predicted[index] == actual[index] for index in certified)
    n_certified = len(certified)
    accuracy = correct / n_certified if n_certified else None
    return SelectiveMetrics(
        n_total=len(actual),
        n_certified=n_certified,
        n_correct=correct,
        coverage=n_certified / len(actual),
        selective_accuracy=accuracy,
        selective_risk=None if accuracy is None else 1.0 - accuracy,
    )


def _select_strongest(
    decisions: tuple[int, ...],
    strengths: Sequence[float],
    count: int,
    *,
    name: str,
) -> tuple[int, ...]:
    clean_strengths = tuple(float(value) for value in strengths)
    if len(decisions) != len(clean_strengths):
        raise ValueError(f"{name} decisions and strengths must have equal length")
    if any(not math.isfinite(value) or value < 0.0 for value in clean_strengths):
        raise ValueError(f"{name} strengths must be finite and non-negative")
    candidates = [index for index, decision in enumerate(decisions) if decision != 0]
    if count > len(candidates):
        raise ValueError(f"target_count exceeds the certified count for {name}")
    # The index tie break is part of the deterministic evaluation contract.
    selected = sorted(candidates, key=lambda index: (-clean_strengths[index], index))[:count]
    return tuple(sorted(selected))


def matched_coverage_metrics(
    decisions_a: Sequence[int],
    strengths_a: Sequence[float],
    decisions_b: Sequence[int],
    strengths_b: Sequence[float],
    truth: Sequence[int],
    *,
    target_count: int | None = None,
    confidence: float = 0.95,
) -> MatchedCoverageMetrics:
    """Compare two selective rules after matching their certified coverage.

    Each method is down-selected independently by a pre-specified strength;
    labels are never used for selection.  If ``target_count`` is omitted, the
    smaller of the two available certified cohorts is used.  Equal strengths
    are resolved by original row index.
    """

    confidence = _validate_alpha(confidence, name="confidence")
    method_a = _validated_decisions(decisions_a, name="method_a")
    method_b = _validated_decisions(decisions_b, name="method_b")
    actual = _validated_truth(truth)
    if not actual:
        raise ValueError("inputs must be non-empty")
    if len(method_a) != len(actual) or len(method_b) != len(actual):
        raise ValueError("both decision arrays and truth must have equal length")
    available_a = sum(value != 0 for value in method_a)
    available_b = sum(value != 0 for value in method_b)
    if target_count is None:
        count = min(available_a, available_b)
    else:
        if isinstance(target_count, bool) or not isinstance(target_count, int):
            raise TypeError("target_count must be an integer or None")
        if target_count < 0:
            raise ValueError("target_count must be non-negative")
        count = target_count
    selected_a = _select_strongest(method_a, strengths_a, count, name="method_a")
    selected_b = _select_strongest(method_b, strengths_b, count, name="method_b")
    selected_a_set = set(selected_a)
    selected_b_set = set(selected_b)
    masked_a = tuple(value if index in selected_a_set else 0 for index, value in enumerate(method_a))
    masked_b = tuple(value if index in selected_b_set else 0 for index, value in enumerate(method_b))
    metrics_a = selective_metrics(masked_a, actual)
    metrics_b = selective_metrics(masked_b, actual)
    if count:
        difference = metrics_a.n_correct / count - metrics_b.n_correct / count
        difference_interval = wilson_difference_interval(
            metrics_a.n_correct,
            count,
            metrics_b.n_correct,
            count,
            confidence=confidence,
        )
    else:
        difference = None
        difference_interval = None
    return MatchedCoverageMetrics(
        target_count=count,
        target_coverage=count / len(actual),
        method_a=metrics_a,
        method_b=metrics_b,
        selected_indices_a=selected_a,
        selected_indices_b=selected_b,
        accuracy_difference=difference,
        accuracy_difference_interval=difference_interval,
    )


def _ordered_block_runs(block_ids: Sequence[Hashable]) -> tuple[tuple[Hashable, tuple[int, ...]], ...]:
    if not block_ids:
        raise ValueError("block_ids must be non-empty")
    runs: list[tuple[Hashable, list[int]]] = []
    completed: set[Hashable] = set()
    for index, block in enumerate(block_ids):
        try:
            is_same = bool(runs) and block == runs[-1][0]
            if is_same:
                runs[-1][1].append(index)
                continue
            if block in completed:
                raise ValueError("each block id must occupy one contiguous run")
            if runs:
                completed.add(runs[-1][0])
            runs.append((block, [index]))
        except TypeError as error:
            raise TypeError("block ids must be hashable") from error
    return tuple((block, tuple(indices)) for block, indices in runs)


def _make_blocked_split(
    runs: Sequence[tuple[Hashable, tuple[int, ...]]],
    calibration_slice: slice,
    gap_slice: slice,
    test_slice: slice,
) -> BlockedSplit:
    calibration_runs = runs[calibration_slice]
    gap_runs = runs[gap_slice]
    test_runs = runs[test_slice]

    def blocks(selected: Sequence[tuple[Hashable, tuple[int, ...]]]) -> tuple[Hashable, ...]:
        return tuple(block for block, _ in selected)

    def indices(selected: Sequence[tuple[Hashable, tuple[int, ...]]]) -> tuple[int, ...]:
        return tuple(index for _, members in selected for index in members)

    return BlockedSplit(
        calibration_indices=indices(calibration_runs),
        gap_indices=indices(gap_runs),
        test_indices=indices(test_runs),
        calibration_blocks=blocks(calibration_runs),
        gap_blocks=blocks(gap_runs),
        test_blocks=blocks(test_runs),
    )


def blocked_calibration_test_split(
    block_ids: Sequence[Hashable],
    *,
    calibration_fraction: float | None = None,
    calibration_blocks: int | None = None,
    gap_blocks: int = 0,
) -> BlockedSplit:
    """Split ordered, contiguous blocks into calibration / embargo / test.

    Exactly one of ``calibration_fraction`` and ``calibration_blocks`` may be
    supplied.  The default is a 50% calibration prefix.  Fractional requests
    use ``floor(n_blocks * fraction)`` and never split a block.  The gap blocks
    immediately following calibration are excluded from both fitted and test
    statistics.
    """

    runs = _ordered_block_runs(block_ids)
    n_blocks = len(runs)
    if calibration_fraction is not None and calibration_blocks is not None:
        raise ValueError("specify calibration_fraction or calibration_blocks, not both")
    if isinstance(gap_blocks, bool) or not isinstance(gap_blocks, int):
        raise TypeError("gap_blocks must be an integer")
    if gap_blocks < 0:
        raise ValueError("gap_blocks must be non-negative")
    if calibration_blocks is None:
        fraction = 0.5 if calibration_fraction is None else float(calibration_fraction)
        if not math.isfinite(fraction) or not 0.0 < fraction < 1.0:
            raise ValueError("calibration_fraction must be finite and between zero and one")
        n_calibration = math.floor(n_blocks * fraction)
    else:
        if isinstance(calibration_blocks, bool) or not isinstance(calibration_blocks, int):
            raise TypeError("calibration_blocks must be an integer")
        n_calibration = calibration_blocks
    if n_calibration <= 0:
        raise ValueError("the split must contain at least one calibration block")
    test_start = n_calibration + gap_blocks
    if test_start >= n_blocks:
        raise ValueError("the split must contain at least one test block after the gap")
    return _make_blocked_split(
        runs,
        slice(0, n_calibration),
        slice(n_calibration, test_start),
        slice(test_start, n_blocks),
    )


def rolling_blocked_splits(
    block_ids: Sequence[Hashable],
    *,
    calibration_blocks: int,
    test_blocks: int,
    gap_blocks: int = 0,
    step_blocks: int = 1,
) -> tuple[BlockedSplit, ...]:
    """Return fixed-width forward splits while keeping every block intact."""

    parameters = {
        "calibration_blocks": calibration_blocks,
        "test_blocks": test_blocks,
        "gap_blocks": gap_blocks,
        "step_blocks": step_blocks,
    }
    for name, value in parameters.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
    if calibration_blocks <= 0 or test_blocks <= 0 or step_blocks <= 0:
        raise ValueError("calibration_blocks, test_blocks, and step_blocks must be positive")
    if gap_blocks < 0:
        raise ValueError("gap_blocks must be non-negative")
    runs = _ordered_block_runs(block_ids)
    width = calibration_blocks + gap_blocks + test_blocks
    splits: list[BlockedSplit] = []
    for start in range(0, len(runs) - width + 1, step_blocks):
        calibration_end = start + calibration_blocks
        test_start = calibration_end + gap_blocks
        test_end = test_start + test_blocks
        splits.append(
            _make_blocked_split(
                runs,
                slice(start, calibration_end),
                slice(calibration_end, test_start),
                slice(test_start, test_end),
            )
        )
    return tuple(splits)
