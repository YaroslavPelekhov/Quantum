"""Information calculations and adversarial witnesses for drift-aware QAE."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .drift_models import anchor_probability, target_probability, total_variation


@dataclass(frozen=True)
class FisherBlock:
    theta_theta: float
    theta_nuisance: float
    nuisance_nuisance: float
    efficient_theta: float


@dataclass(frozen=True)
class ConfoundingWitness:
    theta_first: float
    theta_second: float
    visibility_first: tuple[float, ...]
    visibility_second: tuple[float, ...]
    total_variation_first: float
    total_variation_second: float
    maximum_probability_gap: float


def _binary_fisher(probability: float) -> float:
    return 1.0 / (probability * (1.0 - probability))


def visibility_fisher_block(
    theta: float,
    depth: int,
    visibility: float,
    target_shots: int,
    anchor_shots: int,
) -> FisherBlock:
    """Fisher block when each round has its own unknown visibility."""

    phase = 2.0 * depth * theta
    target = float(target_probability(theta, depth, visibility))
    anchor = float(anchor_probability(visibility))
    derivative_theta = -visibility * depth * np.sin(phase)
    derivative_visibility = 0.5 * np.cos(phase)
    target_weight = target_shots * _binary_fisher(target)
    anchor_weight = anchor_shots * _binary_fisher(anchor)
    theta_theta = target_weight * derivative_theta**2
    theta_nuisance = target_weight * derivative_theta * derivative_visibility
    nuisance_nuisance = target_weight * derivative_visibility**2 + 0.25 * anchor_weight
    if nuisance_nuisance <= 0:
        efficient = theta_theta
    else:
        efficient = max(0.0, theta_theta - theta_nuisance**2 / nuisance_nuisance)
    return FisherBlock(theta_theta, theta_nuisance, nuisance_nuisance, efficient)


def known_visibility_fisher(
    theta: float,
    depths: np.ndarray,
    visibilities: np.ndarray,
    target_shots: int,
) -> float:
    total = 0.0
    for depth, visibility in zip(depths, visibilities, strict=True):
        phase = 2.0 * int(depth) * theta
        probability = float(target_probability(theta, int(depth), float(visibility)))
        derivative = -float(visibility) * int(depth) * np.sin(phase)
        total += target_shots * derivative**2 * _binary_fisher(probability)
    return float(total)


def per_round_efficient_fisher(
    theta: float,
    depths: np.ndarray,
    visibilities: np.ndarray,
    target_shots: int,
    anchor_shots: int,
) -> float:
    return float(
        sum(
            visibility_fisher_block(
                theta,
                int(depth),
                float(visibility),
                target_shots,
                anchor_shots,
            ).efficient_theta
            for depth, visibility in zip(depths, visibilities, strict=True)
        )
    )


def stationary_visibility_fisher(
    theta: float,
    depths: np.ndarray,
    visibility: float,
    target_shots: int,
    anchor_shots: int,
) -> float:
    """Efficient information when one unknown visibility is shared by all rounds."""

    blocks = [
        visibility_fisher_block(theta, int(depth), visibility, target_shots, anchor_shots)
        for depth in depths
    ]
    theta_theta = sum(block.theta_theta for block in blocks)
    theta_nuisance = sum(block.theta_nuisance for block in blocks)
    nuisance_nuisance = sum(block.nuisance_nuisance for block in blocks)
    if nuisance_nuisance <= 0:
        return float(theta_theta)
    return float(max(0.0, theta_theta - theta_nuisance**2 / nuisance_nuisance))


def physical_depth_budget(depths: np.ndarray, target_shots: int, anchor_shots: int) -> int:
    return int(np.sum(depths) * (target_shots + anchor_shots))


def fit_power_law(budgets: np.ndarray, errors: np.ndarray, tail: int = 4) -> dict[str, float]:
    budgets = np.asarray(budgets, dtype=float)
    errors = np.asarray(errors, dtype=float)
    valid = np.isfinite(errors) & (errors > 0) & (budgets > 0)
    budgets = budgets[valid]
    errors = errors[valid]
    if len(budgets) < 2:
        return {"slope": float("nan"), "intercept": float("nan"), "r_squared": float("nan")}
    count = min(tail, len(budgets))
    x = np.log(budgets[-count:])
    y = np.log(errors[-count:])
    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * x + intercept
    residual = float(np.sum((y - prediction) ** 2))
    total = float(np.sum((y - float(np.mean(y))) ** 2))
    r_squared = 1.0 if total == 0 else 1.0 - residual / total
    return {"slope": float(slope), "intercept": float(intercept), "r_squared": r_squared}


def construct_visibility_confounding_witness(
    theta_first: float,
    theta_second: float,
    depths: np.ndarray,
    visibility_bounds: tuple[float, float],
    cosine_floor: float = 1e-5,
) -> ConfoundingWitness | None:
    """Construct two exact unanchored observation laws, if interval geometry permits.

    The first visibility is constant.  The second is chosen so that
    ``v0*cos(2*k*theta0) == v1[k]*cos(2*k*theta1)`` at every depth.
    """

    lower, upper = visibility_bounds
    first_cosine = np.cos(2.0 * np.asarray(depths, dtype=float) * theta_first)
    second_cosine = np.cos(2.0 * np.asarray(depths, dtype=float) * theta_second)
    if np.any(np.abs(first_cosine) < cosine_floor) or np.any(np.abs(second_cosine) < cosine_floor):
        return None
    ratio = first_cosine / second_cosine
    if np.any(ratio <= 0):
        return None
    feasible_lower = max(lower, float(np.max(lower / ratio)))
    feasible_upper = min(upper, float(np.min(upper / ratio)))
    if feasible_lower > feasible_upper:
        return None
    first_visibility = np.full(len(depths), feasible_lower, dtype=float)
    second_visibility = feasible_lower * ratio
    first_probability = target_probability(theta_first, depths, first_visibility)
    second_probability = target_probability(theta_second, depths, second_visibility)
    return ConfoundingWitness(
        theta_first=theta_first,
        theta_second=theta_second,
        visibility_first=tuple(float(value) for value in first_visibility),
        visibility_second=tuple(float(value) for value in second_visibility),
        total_variation_first=total_variation(first_visibility),
        total_variation_second=total_variation(second_visibility),
        maximum_probability_gap=float(np.max(np.abs(first_probability - second_probability))),
    )


def search_visibility_confounding_witness(
    separation: float,
    depths: np.ndarray,
    visibility_bounds: tuple[float, float],
    theta_bounds: tuple[float, float],
    points: int,
    variation_budget: float,
) -> ConfoundingWitness | None:
    """Search a frozen grid for the lowest-TV exact witness at one separation."""

    low, high = theta_bounds
    candidates: list[ConfoundingWitness] = []
    for theta_first in np.linspace(low, high - separation, points):
        witness = construct_visibility_confounding_witness(
            float(theta_first),
            float(theta_first + separation),
            depths,
            visibility_bounds,
        )
        if witness is not None and witness.total_variation_second <= variation_budget + 1e-12:
            candidates.append(witness)
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item.total_variation_second, item.theta_first))


def le_cam_absolute_risk_lower_bound(separation: float, kl_divergence: float) -> float:
    """A conservative two-point absolute-error lower bound via Pinsker."""

    total_variation_bound = min(1.0, np.sqrt(max(0.0, kl_divergence) / 2.0))
    return float(0.25 * separation * (1.0 - total_variation_bound))

