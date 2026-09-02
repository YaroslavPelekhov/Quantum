"""Time-domain model and local estimators for the curvature-boundary screen."""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
from scipy.integrate import quad


Drift = Callable[[float], float]


def rtr_intervals(duration: float) -> tuple[tuple[float, float], ...]:
    if duration <= 0:
        raise ValueError("duration must be positive")
    return (
        (-1.5 * duration, -0.5 * duration),
        (-0.5 * duration, 0.5 * duration),
        (0.5 * duration, 1.5 * duration),
    )


def interval_average(function: Drift, interval: tuple[float, float]) -> float:
    start, end = interval
    value, _ = quad(function, start, end, epsabs=1e-13, epsrel=1e-13, limit=200)
    return float(value / (end - start))


def rtr_drift_averages(function: Drift, duration: float) -> tuple[float, float, float]:
    return tuple(interval_average(function, interval) for interval in rtr_intervals(duration))


def rtr_interpolation_bias(function: Drift, duration: float) -> float:
    left, target, right = rtr_drift_averages(function, duration)
    return float(target - 0.5 * (left + right))


def affine_drift(offset: float, slope: float) -> Drift:
    return lambda time: offset + slope * time


def quadratic_drift(curvature: float) -> Drift:
    return lambda time: 0.5 * curvature * time**2


def compact_target_bump(curvature_bound: float, duration: float, sign: float = 1.0) -> Drift:
    """A C2 bump supported on the target interval with |d''| <= curvature_bound."""

    amplitude = sign * curvature_bound * duration**2 / 24.0

    def bump(time: float) -> float:
        coordinate = 2.0 * time / duration
        if abs(coordinate) >= 1.0:
            return 0.0
        return amplitude * (1.0 - coordinate**2) ** 3

    return bump


def compact_bump_target_average(curvature_bound: float, duration: float) -> float:
    """Exact average of the registered compact bump over the target interval."""

    return 2.0 * curvature_bound * duration**2 / 105.0


def compact_bump_second_derivative(time: np.ndarray, curvature_bound: float, duration: float) -> np.ndarray:
    coordinate = 2.0 * np.asarray(time, dtype=float) / duration
    inside = np.abs(coordinate) < 1.0
    result = np.zeros_like(coordinate)
    # g''(x) = -6 + 36 x^2 - 30 x^4 and d^2/dt^2 contributes 4/T^2.
    result[inside] = (
        curvature_bound
        / 6.0
        * (-6.0 + 36.0 * coordinate[inside] ** 2 - 30.0 * coordinate[inside] ** 4)
    )
    return result


def phasor_probabilities(phase: float, visibility: float) -> tuple[float, float]:
    cosine = float(np.clip(0.5 * (1.0 + visibility * math.cos(phase)), 1e-12, 1.0 - 1e-12))
    sine = float(np.clip(0.5 * (1.0 + visibility * math.sin(phase)), 1e-12, 1.0 - 1e-12))
    return cosine, sine


def sample_local_phase(
    rng: np.random.Generator,
    phase: float,
    visibility: float,
    shots: int,
    trials: int,
) -> np.ndarray:
    cosine_probability, sine_probability = phasor_probabilities(phase, visibility)
    cosine_counts = rng.binomial(shots, cosine_probability, size=trials)
    sine_counts = rng.binomial(shots, sine_probability, size=trials)
    cosine = 2.0 * cosine_counts / shots - 1.0
    sine = 2.0 * sine_counts / shots - 1.0
    wrapped = np.arctan2(sine, cosine)
    # Phase-0 is a local-stage theorem: an earlier coarse stage supplies the branch.
    return wrapped + 2.0 * math.pi * np.rint((phase - wrapped) / (2.0 * math.pi))


def simulate_rtr_local_estimator(
    rng: np.random.Generator,
    theta: float,
    reference_theta: float,
    depth: int,
    duration: float,
    drift: Drift,
    visibility: float,
    shots: int,
    trials: int,
) -> np.ndarray:
    left_drift, target_drift, right_drift = rtr_drift_averages(drift, duration)
    phases = (
        2.0 * depth * (reference_theta + left_drift),
        2.0 * depth * (theta + target_drift),
        2.0 * depth * (reference_theta + right_drift),
    )
    left = sample_local_phase(rng, phases[0], visibility, shots, trials)
    target = sample_local_phase(rng, phases[1], visibility, shots, trials)
    right = sample_local_phase(rng, phases[2], visibility, shots, trials)
    return reference_theta + (target - 0.5 * (left + right)) / (2.0 * depth)


def physical_depth_cost(depth: int, shots: int) -> int:
    """Three circuits times two quadratures, all at the registered depth."""

    return 6 * depth * shots


def fit_log_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    slope, intercept = np.polyfit(np.log(x), np.log(y), 1)
    prediction = slope * np.log(x) + intercept
    residual = float(np.sum((np.log(y) - prediction) ** 2))
    total = float(np.sum((np.log(y) - float(np.mean(np.log(y)))) ** 2))
    return float(slope), float(1.0 - residual / total if total else 1.0)

