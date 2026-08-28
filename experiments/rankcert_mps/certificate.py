"""Rigorous accumulated-angle certificate for normalized MPS truncations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


WEIGHT_TOLERANCE = 1e-12
# Empirical floating-point allowance, calibrated before resuming Phase III from
# the immutable zero-truncation cross-case controls (maximum TVD 2.240e-8).
NUMERICAL_SIMULATION_TOLERANCE = 1e-7


@dataclass(frozen=True)
class CertificateResult:
    epsilon: float
    accumulated_angle: float
    raw_angle_sum: float
    weights: tuple[float, ...]
    saturated: bool


def validated_weight(value: float, tolerance: float = WEIGHT_TOLERANCE) -> float:
    weight = float(value)
    if not math.isfinite(weight):
        raise ValueError(f"Discarded weight must be finite, got {value!r}")
    if weight < -tolerance:
        raise ValueError(f"Discarded weight is genuinely negative: {weight}")
    if weight > 1.0 + tolerance:
        raise ValueError(f"Discarded weight exceeds one: {weight}")
    return min(1.0, max(0.0, weight))


def accumulated_angle_certificate(
    discarded_weights: Iterable[float], tolerance: float = WEIGHT_TOLERANCE
) -> CertificateResult:
    weights = tuple(validated_weight(value, tolerance) for value in discarded_weights)
    raw_angle = math.fsum(math.asin(math.sqrt(weight)) for weight in weights)
    angle = min(math.pi / 2.0, raw_angle)
    return CertificateResult(
        epsilon=math.sin(angle),
        accumulated_angle=angle,
        raw_angle_sum=raw_angle,
        weights=weights,
        saturated=raw_angle >= math.pi / 2.0,
    )


def clipped_interval(probability: float, epsilon: float) -> tuple[float, float]:
    probability = float(probability)
    epsilon = float(epsilon)
    if not (math.isfinite(probability) and 0.0 <= probability <= 1.0):
        raise ValueError(f"Invalid probability: {probability}")
    if not (math.isfinite(epsilon) and 0.0 <= epsilon <= 1.0):
        raise ValueError(f"Invalid epsilon: {epsilon}")
    return max(0.0, probability - epsilon), min(1.0, probability + epsilon)


def ranking_certificate(
    p_lr: float, epsilon_lr: float, p_mr: float, epsilon_mr: float
) -> dict:
    lr_interval = clipped_interval(p_lr, epsilon_lr)
    mr_interval = clipped_interval(p_mr, epsilon_mr)
    delta = float(p_mr) - float(p_lr)
    epsilon_pair = float(epsilon_lr) + float(epsilon_mr)
    certified = abs(delta) > epsilon_pair
    sign = 1 if delta > 0 else -1 if delta < 0 else 0
    return {
        "mps_delta": delta,
        "epsilon_pair": epsilon_pair,
        "lr_interval": lr_interval,
        "mr_interval": mr_interval,
        "certified": certified,
        "certified_sign": sign if certified else None,
        "normalized_certificate_ratio": (
            epsilon_pair / abs(delta) if delta != 0.0 else math.inf
        ),
    }
