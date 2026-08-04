from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    net_gain: float
    mean_gain: float
    positive_fraction: float
    backend_coverage: int
    reason: str


def held_out_promotion_gate(
    baseline_scores: Mapping[str, float],
    operator_scores: Mapping[str, float],
    complexity_cost: float,
    complexity_weight: float = 0.02,
    min_positive_fraction: float = 0.60,
    min_backend_coverage: int = 2,
    backend_by_case: Mapping[str, str] | None = None,
) -> PromotionDecision:
    """RG-HLI-style operator promotion using only held-out cases.

    Keys must identify the same held-out instance/backend/seed cases. The gate
    prevents admission when a mean gain is caused by one exceptional case.
    """
    if set(baseline_scores) != set(operator_scores):
        raise ValueError("Baseline and operator scores must cover identical held-out cases")
    if not baseline_scores:
        raise ValueError("At least one held-out case is required")

    gains = [operator_scores[k] - baseline_scores[k] for k in baseline_scores]
    avg_gain = mean(gains)
    positive_fraction = sum(g > 0 for g in gains) / len(gains)
    net_gain = avg_gain - complexity_weight * complexity_cost

    if backend_by_case is None:
        coverage = min_backend_coverage
    else:
        missing = set(baseline_scores) - set(backend_by_case)
        if missing:
            raise ValueError(f"Missing backend labels for cases: {sorted(missing)}")
        coverage = len({backend_by_case[k] for k in baseline_scores})

    promote = (
        net_gain > 0
        and positive_fraction >= min_positive_fraction
        and coverage >= min_backend_coverage
    )
    reason = (
        "held-out gain exceeds complexity and transfers across cases/backends"
        if promote
        else "rejected: insufficient robust held-out transfer after complexity penalty"
    )
    return PromotionDecision(
        promote=promote,
        net_gain=net_gain,
        mean_gain=avg_gain,
        positive_fraction=positive_fraction,
        backend_coverage=coverage,
        reason=reason,
    )
