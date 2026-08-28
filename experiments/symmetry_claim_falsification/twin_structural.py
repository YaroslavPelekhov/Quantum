"""Amplitude-blind structural bounds in a cut-local twin-count basis."""

from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching


def count_labels(
    indices: np.ndarray,
    groups: tuple[tuple[int, ...], ...],
    positions: set[int],
) -> np.ndarray:
    """Return one integer count-vector label per full computational index."""
    values = np.asarray(indices, dtype=np.int64).reshape(-1)
    counts = np.empty((values.size, len(groups)), dtype=np.int16)
    radices = []
    for column, group in enumerate(groups):
        selected = tuple(position for position in group if position in positions)
        count = np.zeros(values.size, dtype=np.int16)
        for position in selected:
            count += ((values >> position) & 1).astype(np.int16)
        counts[:, column] = count
        radices.append(len(selected) + 1)
    return np.ravel_multi_index(counts.T, tuple(radices)).astype(np.int64)


def twin_frontier_profile(
    event_indices: np.ndarray,
    qubits: int,
    groups: tuple[tuple[int, ...], ...],
) -> list[dict]:
    """Capacity-two event bound after quotienting cut-local twin actions."""
    rows = []
    for cut in range(1, qubits):
        boundary = qubits - cut
        left_positions = set(range(boundary, qubits))
        right_positions = set(range(boundary))
        left = count_labels(event_indices, groups, left_positions)
        right = count_labels(event_indices, groups, right_positions)
        pairs = np.unique(np.column_stack((left, right)), axis=0)
        left_values, left_inverse = np.unique(pairs[:, 0], return_inverse=True)
        right_values, right_inverse = np.unique(pairs[:, 1], return_inverse=True)
        s_left = int(left_values.size)
        s_right = int(right_values.size)
        graph_rows = np.repeat(left_inverse, 2)
        graph_columns = np.column_stack(
            (2 * right_inverse, 2 * right_inverse + 1)
        ).reshape(-1)
        graph = coo_matrix(
            (np.ones(graph_rows.size, dtype=np.int8), (graph_rows, graph_columns)),
            shape=(s_left, 2 * s_right),
        ).tocsr()
        matching = maximum_bipartite_matching(graph, perm_type="column")
        width = int(np.count_nonzero(matching >= 0))
        left_orbit_dimension = int(np.prod([
            1 + sum(position in left_positions for position in group)
            for group in groups
        ]))
        bound = min(2 * s_left, 4 * s_right, 2 * width, left_orbit_dimension)
        rows.append({
            "cut": cut,
            "dense_left_dimension": 1 << cut,
            "left_orbit_dimension": left_orbit_dimension,
            "quotient_event_edges": int(pairs.shape[0]),
            "quotient_s_left": s_left,
            "quotient_s_right": s_right,
            "quotient_paired_matching_width": width,
            "twin_structural_bound": int(bound),
        })
    return rows
