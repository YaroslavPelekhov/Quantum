"""Exact low-rank structural audit utilities for diagonal decision events."""

from __future__ import annotations

import hashlib

import numpy as np
from scipy import linalg
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching


RANK_TOLERANCE = 1e-12


def split_event_indices(event_indices: np.ndarray, qubits: int, cut: int):
    if not 0 < cut < qubits:
        raise ValueError("cut must be nontrivial")
    right_dimension = 1 << (qubits - cut)
    indices = np.asarray(event_indices, dtype=np.int64)
    left = indices // right_dimension
    right = indices % right_dimension
    return left, right


def frontier_profile(event_indices: np.ndarray, qubits: int) -> list[dict]:
    rows = []
    for cut in range(1, qubits):
        left, right = split_event_indices(event_indices, qubits, cut)
        left_values, left_inverse = np.unique(left, return_inverse=True)
        right_values, right_inverse = np.unique(right, return_inverse=True)
        s_left = int(left_values.size)
        s_right = int(right_values.size)
        # Each event edge supplies one independent coefficient for each of the
        # two compared states.  The generic rank of their stacked coefficient
        # pattern is bounded by a bipartite matching with capacity two on every
        # right suffix, represented here by duplicating the right vertices.
        graph_rows = np.repeat(left_inverse, 2)
        graph_columns = np.column_stack(
            (2 * right_inverse, 2 * right_inverse + 1)
        ).reshape(-1)
        graph = coo_matrix(
            (np.ones(graph_rows.size, dtype=np.int8), (graph_rows, graph_columns)),
            shape=(s_left, 2 * s_right),
        ).tocsr()
        matching = maximum_bipartite_matching(graph, perm_type="column")
        paired_matching_width = int(np.count_nonzero(matching >= 0))
        dimension = 1 << cut
        rows.append({
            "cut": cut,
            "left_dimension": dimension,
            "s_left": s_left,
            "s_right": s_right,
            "left_bound": 2 * s_left,
            "right_bound": 4 * s_right,
            "paired_matching_width": paired_matching_width,
            "matching_bound": 2 * paired_matching_width,
            "structural_bound": min(
                2 * s_left,
                4 * s_right,
                2 * paired_matching_width,
                dimension,
            ),
        })
    return rows


def _left_factors(
    state_a: np.ndarray,
    state_b: np.ndarray,
    event_indices: np.ndarray,
    qubits: int,
    cut: int,
) -> tuple[np.ndarray, np.ndarray]:
    dimension = 1 << cut
    right_dimension = 1 << (qubits - cut)
    a = np.asarray(state_a).reshape(dimension, right_dimension)
    b = np.asarray(state_b).reshape(dimension, right_dimension)
    event_left, event_right = split_event_indices(event_indices, qubits, cut)
    prefixes = np.unique(event_left)
    support = np.zeros((dimension, prefixes.size), dtype=np.complex128)
    support[prefixes, np.arange(prefixes.size)] = 1.0
    contrast = np.empty_like(support)
    for column, prefix in enumerate(prefixes):
        suffixes = event_right[event_left == prefix]
        contrast[:, column] = (
            b[:, suffixes] @ b[prefix, suffixes].conj()
            - a[:, suffixes] @ a[prefix, suffixes].conj()
        )
    factors = np.concatenate((support, contrast), axis=1)
    size = prefixes.size
    metric = np.zeros((2 * size, 2 * size), dtype=np.complex128)
    metric[:size, size:] = 0.5 * np.eye(size)
    metric[size:, :size] = 0.5 * np.eye(size)
    return factors, metric


def _right_factors(
    state_a: np.ndarray,
    state_b: np.ndarray,
    event_indices: np.ndarray,
    qubits: int,
    cut: int,
) -> tuple[np.ndarray, np.ndarray]:
    dimension = 1 << cut
    right_dimension = 1 << (qubits - cut)
    a = np.asarray(state_a).reshape(dimension, right_dimension)
    b = np.asarray(state_b).reshape(dimension, right_dimension)
    event_left, event_right = split_event_indices(event_indices, qubits, cut)
    suffixes = np.unique(event_right)
    count = suffixes.size
    u_b = np.zeros((dimension, count), dtype=np.complex128)
    u_a = np.zeros_like(u_b)
    for column, suffix in enumerate(suffixes):
        prefixes = event_left[event_right == suffix]
        u_b[prefixes, column] = b[prefixes, suffix]
        u_a[prefixes, column] = a[prefixes, suffix]
    v_b = np.asarray(b[:, suffixes], dtype=np.complex128)
    v_a = np.asarray(a[:, suffixes], dtype=np.complex128)
    factors = np.concatenate((u_b, v_b, u_a, v_a), axis=1)
    metric = np.zeros((4 * count, 4 * count), dtype=np.complex128)
    eye = 0.5 * np.eye(count)
    metric[:count, count:2 * count] = eye
    metric[count:2 * count, :count] = eye
    metric[2 * count:3 * count, 3 * count:] = -eye
    metric[3 * count:, 2 * count:3 * count] = -eye
    return factors, metric


def low_rank_spectrum(
    state_a: np.ndarray,
    state_b: np.ndarray,
    event_indices: np.ndarray,
    cut: int,
) -> dict:
    size = int(state_a.size)
    qubits = int(round(np.log2(size)))
    if state_a.shape != state_b.shape or size != 1 << qubits:
        raise ValueError("states must be equally sized power-of-two vectors")
    left, right = split_event_indices(event_indices, qubits, cut)
    s_left = int(np.unique(left).size)
    s_right = int(np.unique(right).size)
    if 2 * s_left <= 4 * s_right:
        factors, metric = _left_factors(
            state_a, state_b, event_indices, qubits, cut
        )
        factorization = "left-prefix"
    else:
        factors, metric = _right_factors(
            state_a, state_b, event_indices, qubits, cut
        )
        factorization = "right-suffix"
    _, triangular = linalg.qr(
        factors, mode="economic", check_finite=False, overwrite_a=True
    )
    core = triangular @ metric @ triangular.conj().T
    values = linalg.eigvalsh(core, check_finite=False)
    values = values[np.argsort(np.abs(values))[::-1]]
    numerical_rank = int(np.count_nonzero(np.abs(values) > RANK_TOLERANCE))
    return {
        "factorization": factorization,
        "factor_columns": int(metric.shape[0]),
        "numerical_rank": numerical_rank,
        "spectral_norm": float(np.max(np.abs(values), initial=0.0)),
        "trace": float(values.sum(dtype=np.float64)),
        "trace_norm": float(np.abs(values).sum(dtype=np.float64)),
        "smallest_retained_abs_eigenvalue": (
            float(np.abs(values[numerical_rank - 1])) if numerical_rank else 0.0
        ),
        "largest_discarded_abs_eigenvalue": (
            float(np.abs(values[numerical_rank]))
            if numerical_rank < values.size else 0.0
        ),
    }


def deterministic_seed(*parts: str) -> int:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def haar_pair(size: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    states = []
    for _ in range(2):
        state = rng.standard_normal(size) + 1j * rng.standard_normal(size)
        state = np.asarray(state, dtype=np.complex128)
        state /= np.linalg.norm(state)
        states.append(state)
    return states[0], states[1]


def tensor_train_ranks(
    state: np.ndarray, tolerance: float = RANK_TOLERANCE
) -> list[int]:
    """Return sequential Schmidt ranks using a tolerance-truncated TT-SVD."""
    size = int(state.size)
    qubits = int(round(np.log2(size)))
    if state.ndim != 1 or size != 1 << qubits:
        raise ValueError("state must be a power-of-two vector")
    work = np.asarray(state, dtype=np.complex128).reshape(2, -1)
    ranks = []
    for cut in range(1, qubits):
        _, singular, right = linalg.svd(
            work,
            full_matrices=False,
            check_finite=False,
            overwrite_a=True,
            lapack_driver="gesdd",
        )
        rank = int(np.count_nonzero(singular > tolerance))
        ranks.append(rank)
        if cut < qubits - 1:
            work = (
                singular[:rank, None] * right[:rank, :]
            ).reshape(rank * 2, -1)
    return ranks
