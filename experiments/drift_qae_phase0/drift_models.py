"""Frozen observation models for the drift-aware amplitude-estimation screen.

The module deliberately keeps two physically different noise models separate:

* ``readout`` applies a depth-independent visibility after the amplified
  experiment;
* ``gate`` accumulates a per-layer rate through the amplification depth.

Both produce a binary observation with centered expectation
``visibility * cos(2 * depth * theta)``.  An anchor has the same visibility
and known ideal centered expectation one.
"""

from __future__ import annotations

import math

import numpy as np


PROBABILITY_EPSILON = 1e-12


def odd_geometric_depths(levels: int) -> np.ndarray:
    """Return the QAE-compatible geometric ladder 1, 3, 7, ..., 2**L-1."""

    if levels < 1:
        raise ValueError("levels must be positive")
    return np.asarray([(1 << (index + 1)) - 1 for index in range(levels)], dtype=int)


def total_variation(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(np.sum(np.abs(np.diff(values))))


def rescaled_drift_path(
    length: int,
    center: float,
    variation: float,
    lower: float,
    upper: float,
    phase: float = 0.31,
) -> np.ndarray:
    """Construct a deterministic held-out path with the requested TV when feasible."""

    if length < 1:
        raise ValueError("length must be positive")
    if not lower < center < upper:
        raise ValueError("center must lie strictly inside the bounds")
    if variation < 0:
        raise ValueError("variation must be nonnegative")
    if length == 1 or variation == 0:
        return np.full(length, center, dtype=float)

    grid = np.linspace(phase, phase + 2.7 * math.pi, length)
    raw = np.sin(grid) + 0.37 * np.sin(2.3 * grid + 0.2)
    raw -= float(np.mean(raw))
    raw_tv = total_variation(raw)
    if raw_tv == 0:
        return np.full(length, center, dtype=float)
    direction = raw / raw_tv
    maximum_scale = min(
        (upper - center) / max(float(np.max(direction)), PROBABILITY_EPSILON),
        (center - lower) / max(float(-np.min(direction)), PROBABILITY_EPSILON),
    )
    scale = min(variation, maximum_scale)
    return center + scale * direction


def readout_visibility(parameter: np.ndarray | float, depth: np.ndarray | float) -> np.ndarray:
    """Depth-independent post-circuit visibility."""

    parameter_array, depth_array = np.broadcast_arrays(
        np.asarray(parameter, dtype=float), np.asarray(depth, dtype=float)
    )
    del depth_array
    return parameter_array.copy()


def gate_visibility(rate: np.ndarray | float, depth: np.ndarray | float) -> np.ndarray:
    """Visibility from a Markovian rate accumulated over amplified depth."""

    return np.exp(-np.asarray(rate, dtype=float) * np.asarray(depth, dtype=float))


def target_probability(theta: float, depth: np.ndarray | float, visibility: np.ndarray | float) -> np.ndarray:
    depth_array = np.asarray(depth, dtype=float)
    visibility_array = np.asarray(visibility, dtype=float)
    probability = 0.5 * (1.0 + visibility_array * np.cos(2.0 * depth_array * theta))
    return np.clip(probability, PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)


def anchor_probability(visibility: np.ndarray | float) -> np.ndarray:
    probability = 0.5 * (1.0 + np.asarray(visibility, dtype=float))
    return np.clip(probability, PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)


def bernoulli_kl(first: np.ndarray | float, second: np.ndarray | float) -> np.ndarray:
    first_array = np.clip(np.asarray(first, dtype=float), PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    second_array = np.clip(np.asarray(second, dtype=float), PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    return first_array * np.log(first_array / second_array) + (1.0 - first_array) * np.log(
        (1.0 - first_array) / (1.0 - second_array)
    )

