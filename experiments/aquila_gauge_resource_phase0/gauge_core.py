"""Core geometry, cochain, and circular gauge-quotient optimization routines."""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix, csr_matrix


@dataclass(frozen=True)
class CubeComplex:
    vertices: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]
    faces: tuple[tuple[int, int, int], ...]
    gradient: csr_matrix
    curl: csr_matrix


def cube_complex(n: int) -> CubeComplex:
    vertices = tuple(range(1 << n))
    edges = tuple((state, site) for state in vertices for site in range(n) if not state & (1 << site))
    edge_index = {edge: index for index, edge in enumerate(edges)}

    gradient_rows: list[int] = []
    gradient_columns: list[int] = []
    gradient_values: list[int] = []
    for row, (state, site) in enumerate(edges):
        gradient_rows.extend((row, row))
        gradient_columns.extend((state, state | (1 << site)))
        gradient_values.extend((-1, 1))
    gradient = coo_matrix(
        (gradient_values, (gradient_rows, gradient_columns)),
        shape=(len(edges), len(vertices)),
        dtype=float,
    ).tocsr()

    faces = tuple(
        (state, first, second)
        for state in vertices
        for first in range(n)
        for second in range(first + 1, n)
        if not state & (1 << first) and not state & (1 << second)
    )
    curl_rows: list[int] = []
    curl_columns: list[int] = []
    curl_values: list[int] = []
    for row, (state, first, second) in enumerate(faces):
        terms = (
            (edge_index[(state, first)], 1),
            (edge_index[(state | (1 << first), second)], 1),
            (edge_index[(state | (1 << second), first)], -1),
            (edge_index[(state, second)], -1),
        )
        for column, value in terms:
            curl_rows.append(row)
            curl_columns.append(column)
            curl_values.append(value)
    curl = coo_matrix(
        (curl_values, (curl_rows, curl_columns)),
        shape=(len(faces), len(edges)),
        dtype=float,
    ).tocsr()
    return CubeComplex(vertices, edges, faces, gradient, curl)


def transition_frequencies(
    n: int,
    positions_um: np.ndarray,
    mask: np.ndarray,
    c6_rad_per_us_um6: float,
    local_detuning_span_rad_per_us: float,
    edges: tuple[tuple[int, int], ...],
) -> tuple[np.ndarray, np.ndarray, float]:
    positions = np.asarray(positions_um[:n], dtype=float)
    onsite = local_detuning_span_rad_per_us * np.asarray(mask[:n], dtype=float)
    interactions = np.zeros((n, n), dtype=float)
    for first in range(n):
        for second in range(first + 1, n):
            distance = float(np.linalg.norm(positions[first] - positions[second]))
            interactions[first, second] = interactions[second, first] = (
                c6_rad_per_us_um6 / distance**6
            )
    frequencies = np.empty(len(edges), dtype=float)
    for row, (state, site) in enumerate(edges):
        occupied = [other for other in range(n) if state & (1 << other)]
        frequencies[row] = onsite[site] + sum(interactions[site, other] for other in occupied)
    width = float(np.ptp(frequencies))
    if not width > 0:
        raise ValueError("transition-frequency width must be positive")
    normalized = (frequencies - float(np.min(frequencies))) / width
    return frequencies, normalized, width


def hashed_edge_phases(
    tag: str,
    n: int,
    target_id: int,
    edges: tuple[tuple[int, int], ...],
    half_range_rad: float,
) -> np.ndarray:
    phases = []
    denominator = float(1 << 64)
    for state, site in edges:
        token = f"{tag}|{n}|{target_id}|{state}|{site}".encode("utf-8")
        integer = int.from_bytes(hashlib.sha256(token).digest()[:8], "big")
        uniform = integer / denominator
        phases.append(half_range_rad * (2.0 * uniform - 1.0))
    return np.asarray(phases, dtype=float)


def wrap_angle(values: np.ndarray) -> np.ndarray:
    return np.angle(np.exp(1j * np.asarray(values, dtype=float)))


def adjacent_spectral_data(frequencies: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(np.asarray(frequencies), kind="stable")
    gaps = np.diff(np.asarray(frequencies)[order])
    if np.any(gaps <= 0):
        raise ValueError("transition frequencies must be distinct")
    return order, gaps


def spectral_cost(phases: np.ndarray, order: np.ndarray, gaps: np.ndarray) -> float:
    differences = wrap_angle(np.diff(np.asarray(phases)[order]))
    return float(np.max(np.abs(differences) / gaps))


def spectral_total_variation(phases: np.ndarray, order: np.ndarray) -> float:
    return float(np.sum(np.abs(wrap_angle(np.diff(np.asarray(phases)[order])))))


def circular_gauge_cost(
    phases: np.ndarray,
    gradient: csr_matrix,
    normalized_frequencies: np.ndarray,
    winding_bound: int = 3,
    relative_mip_gap: float = 1e-7,
    time_limit_seconds: float = 120.0,
) -> dict:
    """Minimize the exact circular adjacent-frequency Lipschitz cost.

    The integer variables select the 2*pi lift independently for each adjacent
    spectral difference.  Vertex zero is fixed to remove the redundant global
    vertex gauge.
    """

    phases = np.asarray(phases, dtype=float)
    order, gaps = adjacent_spectral_data(normalized_frequencies)
    edge_count, vertex_count = gradient.shape
    difference_count = edge_count - 1
    winding_offset = vertex_count
    cost_index = vertex_count + difference_count
    variable_count = cost_index + 1

    ordered_gradient = gradient[order]
    gauge_differences = (ordered_gradient[1:] - ordered_gradient[:-1]).tocoo()
    base_differences = np.diff(phases[order])

    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    upper = np.empty(2 * difference_count, dtype=float)
    for source_row, column, value in zip(
        gauge_differences.row, gauge_differences.col, gauge_differences.data
    ):
        rows.extend((2 * int(source_row), 2 * int(source_row) + 1))
        columns.extend((int(column), int(column)))
        values.extend((float(value), -float(value)))
    for index, (base, gap) in enumerate(zip(base_differences, gaps)):
        rows.extend((2 * index, 2 * index + 1, 2 * index, 2 * index + 1))
        columns.extend((winding_offset + index, winding_offset + index, cost_index, cost_index))
        values.extend((-2.0 * math.pi, 2.0 * math.pi, -float(gap), -float(gap)))
        upper[2 * index] = -float(base)
        upper[2 * index + 1] = float(base)
    constraint_matrix = coo_matrix(
        (values, (rows, columns)), shape=(2 * difference_count, variable_count)
    ).tocsr()

    lower_bounds = np.concatenate(
        (
            np.full(vertex_count, -math.pi),
            np.full(difference_count, -float(winding_bound)),
            np.array([0.0]),
        )
    )
    upper_bounds = np.concatenate(
        (
            np.full(vertex_count, math.pi),
            np.full(difference_count, float(winding_bound)),
            np.array([np.inf]),
        )
    )
    lower_bounds[0] = upper_bounds[0] = 0.0
    integrality = np.zeros(variable_count, dtype=np.uint8)
    integrality[winding_offset:cost_index] = 1
    objective = np.zeros(variable_count, dtype=float)
    objective[cost_index] = 1.0

    started = time.perf_counter()
    result = milp(
        objective,
        integrality=integrality,
        bounds=Bounds(lower_bounds, upper_bounds),
        constraints=LinearConstraint(constraint_matrix, -np.inf, upper),
        options={
            "time_limit": float(time_limit_seconds),
            "mip_rel_gap": float(relative_mip_gap),
            "presolve": True,
        },
    )
    elapsed = time.perf_counter() - started
    row = {
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "elapsed_seconds": elapsed,
        "objective_upper": float(result.fun) if result.fun is not None else math.nan,
        "objective_lower": float(result.get("mip_dual_bound", math.nan)),
        "mip_gap": float(result.get("mip_gap", math.nan)),
        "mip_node_count": int(result.get("mip_node_count", -1)),
        "order": order,
        "frequency_gaps": gaps,
    }
    if result.x is not None:
        theta = np.asarray(result.x[:vertex_count], dtype=float)
        representative = phases + gradient @ theta
        achieved_cost = spectral_cost(representative, order, gaps)
        row.update(
            {
                "theta": theta,
                "representative": representative,
                "achieved_cost": achieved_cost,
                "circular_total_variation": spectral_total_variation(representative, order),
                "constraint_error": max(0.0, achieved_cost - float(result.fun)),
            }
        )
    return row


def fit_log2_scaling(n_values: np.ndarray, values: np.ndarray) -> dict:
    x = np.asarray(n_values, dtype=float)
    y = np.log2(np.asarray(values, dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * x + intercept
    residual = float(np.sum((y - prediction) ** 2))
    total = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 if total == 0.0 and residual == 0.0 else 1.0 - residual / total
    return {"slope": float(slope), "intercept": float(intercept), "r_squared": r_squared}
