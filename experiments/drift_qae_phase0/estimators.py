"""Small estimators used by the frozen drift-QAE Phase-0 screen."""

from __future__ import annotations

import math

import numpy as np

from .drift_models import anchor_probability, target_probability


def anchor_visibility_estimate(successes: int, shots: int, bounds: tuple[float, float]) -> float:
    """Jeffreys-smoothed visibility estimate from a known-positive anchor."""

    if shots <= 0:
        raise ValueError("anchor shots must be positive")
    probability = (successes + 0.5) / (shots + 1.0)
    visibility = 2.0 * probability - 1.0
    return float(np.clip(visibility, bounds[0], bounds[1]))


def cosine_candidates(
    centered_expectation: float,
    depth: int,
    theta_bounds: tuple[float, float],
) -> list[float]:
    """All theta values in bounds compatible with one amplified cosine."""

    alpha = math.acos(float(np.clip(centered_expectation, -1.0, 1.0)))
    low, high = theta_bounds
    candidates: list[float] = []
    maximum_index = int(math.ceil((2.0 * depth * high + alpha) / (2.0 * math.pi))) + 1
    for index in range(-1, maximum_index + 1):
        for signed_alpha in (alpha, -alpha):
            theta = (signed_alpha + 2.0 * math.pi * index) / (2.0 * depth)
            if low - 1e-15 <= theta <= high + 1e-15:
                candidates.append(float(theta))
    return sorted(set(candidates))


def sequential_unwrap_estimate(
    target_successes: np.ndarray,
    target_shots: int,
    depths: np.ndarray,
    visibility_estimates: np.ndarray,
    theta_bounds: tuple[float, float],
) -> tuple[float, bool]:
    """Estimate theta by resolving each amplified fringe against the prior level."""

    current: float | None = None
    branch_failure = False
    for successes, depth, visibility in zip(
        target_successes, depths, visibility_estimates, strict=True
    ):
        empirical_center = 2.0 * float(successes) / target_shots - 1.0
        corrected = empirical_center / max(float(visibility), 1e-9)
        candidates = cosine_candidates(corrected, int(depth), theta_bounds)
        if not candidates:
            branch_failure = True
            continue
        if current is None:
            midpoint = 0.5 * (theta_bounds[0] + theta_bounds[1])
            current = min(candidates, key=lambda value: abs(value - midpoint))
        else:
            spacing = math.pi / int(depth)
            selected = min(candidates, key=lambda value: abs(value - current))
            if abs(selected - current) > 0.45 * spacing:
                branch_failure = True
            current = selected
    if current is None:
        return 0.5 * (theta_bounds[0] + theta_bounds[1]), True
    return float(current), branch_failure


def simulate_amplified_trial(
    rng: np.random.Generator,
    theta: float,
    depths: np.ndarray,
    visibilities: np.ndarray,
    target_shots: int,
    anchor_shots: int,
    visibility_bounds: tuple[float, float],
    theta_bounds: tuple[float, float],
    estimator: str,
    nominal_visibility: float,
) -> dict[str, float | bool]:
    target_probabilities = target_probability(theta, depths, visibilities)
    target_successes = rng.binomial(target_shots, target_probabilities)
    if estimator == "oracle":
        estimates = np.asarray(visibilities, dtype=float)
    elif estimator == "anchored":
        anchor_successes = rng.binomial(anchor_shots, anchor_probability(visibilities))
        estimates = np.asarray(
            [
                anchor_visibility_estimate(int(successes), anchor_shots, visibility_bounds)
                for successes in anchor_successes
            ],
            dtype=float,
        )
    elif estimator == "nominal_unanchored":
        estimates = np.full(len(depths), nominal_visibility, dtype=float)
    else:
        raise ValueError(f"unknown estimator: {estimator}")
    estimate, branch_failure = sequential_unwrap_estimate(
        target_successes,
        target_shots,
        depths,
        estimates,
        theta_bounds,
    )
    return {
        "estimate": estimate,
        "absolute_error": abs(estimate - theta),
        "squared_error": (estimate - theta) ** 2,
        "branch_failure": branch_failure,
    }


def simulate_direct_trial(
    rng: np.random.Generator,
    theta: float,
    physical_budget: int,
    visibility: float,
    theta_bounds: tuple[float, float],
) -> dict[str, float | bool]:
    """Strong k=1 comparator given the true mean visibility for free."""

    probability = float(target_probability(theta, 1, visibility))
    successes = int(rng.binomial(physical_budget, probability))
    empirical_center = 2.0 * successes / physical_budget - 1.0
    corrected = empirical_center / max(visibility, 1e-9)
    candidates = cosine_candidates(corrected, 1, theta_bounds)
    if not candidates:
        estimate = 0.5 * (theta_bounds[0] + theta_bounds[1])
        failed = True
    else:
        estimate = min(candidates, key=lambda value: abs(value - 0.5 * sum(theta_bounds)))
        failed = False
    return {
        "estimate": float(estimate),
        "absolute_error": abs(float(estimate) - theta),
        "squared_error": (float(estimate) - theta) ** 2,
        "branch_failure": failed,
    }
