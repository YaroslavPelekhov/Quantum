"""Sparse-event construction of DCS-RDT operators directly from Aer MPS data."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy import linalg


def enumerate_bks_support(scorer: dict) -> list[int]:
    """Enumerate the frozen unit-weight MIS scorer without a 2**n truth table."""
    weights = [int(value) for value in scorer["weights"]]
    if scorer["impossible"]:
        return []
    if any(value != 1 for value in weights):
        raise ValueError("Sparse MIS enumerator requires unit variable weights")
    qubits = len(weights)
    adjacency = [0] * qubits
    for mask, pattern in scorer["forbidden"]:
        mask = int(mask)
        pattern = int(pattern)
        bits = [index for index in range(qubits) if (mask >> index) & 1]
        if mask != pattern or len(bits) != 2:
            raise ValueError("Sparse MIS enumerator requires pairwise 11 exclusions")
        left, right = bits
        adjacency[left] |= 1 << right
        adjacency[right] |= 1 << left
    required = max(0, int(scorer["bks"]) - int(scorer["constant_selected"]))
    output: list[int] = []

    def visit(position: int, selected: int, count: int) -> None:
        if count + qubits - position < required:
            return
        if position == qubits:
            if count >= required:
                output.append(selected)
            return
        visit(position + 1, selected, count)
        if not selected & adjacency[position]:
            visit(position + 1, selected | (1 << position), count + 1)

    visit(0, 0, 0)
    return sorted(output)


def mps_amplitude(mps, basis_index: int) -> complex:
    gammas, lambdas = mps
    vector = np.ones(1, dtype=np.complex128)
    for qubit, gamma in enumerate(gammas):
        vector = vector @ gamma[(basis_index >> qubit) & 1]
        if qubit < len(lambdas):
            vector = vector * lambdas[qubit]
    return complex(vector[0])


def mps_norm(mps) -> float:
    gammas, lambdas = mps
    environment = np.ones((1, 1), dtype=np.complex128)
    for qubit, gamma in enumerate(gammas):
        updated = None
        for physical in (0, 1):
            tensor = gamma[physical]
            if qubit < len(lambdas):
                tensor = tensor * lambdas[qubit][None, :]
            term = tensor.conj().T @ environment @ tensor
            updated = term if updated is None else updated + term
        environment = updated
    return float(environment[0, 0].real)


def mps_storage_bytes(mps) -> int:
    gammas, lambdas = mps
    return int(
        sum(array.nbytes for pair in gammas for array in pair)
        + sum(array.nbytes for array in lambdas)
    )


def maximum_mps_bond(mps) -> int:
    gammas, _ = mps
    return int(max(max(array.shape) for pair in gammas for array in pair))


def decision_contribution_from_mps(
    mps, support: list[int], cut: int
) -> tuple[np.ndarray, dict]:
    """Construct Tr_R({E,|psi><psi|}/2) using sparse event slices."""
    qubits = len(mps[0])
    if not 0 < cut < qubits:
        raise ValueError("Invalid cut")
    left_dimension = 1 << cut
    right_qubits = qubits - cut
    right_mask = (1 << right_qubits) - 1
    grouped: dict[int, list[int]] = defaultdict(list)
    for index in support:
        grouped[index & right_mask].append(index >> right_qubits)
    raw = np.zeros((left_dimension, left_dimension), dtype=np.complex128)
    amplitude_queries = 0
    for right, selected_left in grouped.items():
        column = np.asarray(
            [
                mps_amplitude(mps, right | (left << right_qubits))
                for left in range(left_dimension)
            ],
            dtype=np.complex128,
        )
        amplitude_queries += left_dimension
        for left in selected_left:
            raw[left, :] += column[left] * column.conj()
    contribution = 0.5 * (raw + raw.conj().T)
    return contribution, {
        "support_rank": len(support),
        "distinct_right_slices": len(grouped),
        "amplitude_queries": amplitude_queries,
        "left_dimension": left_dimension,
    }


def decision_operator_from_mps_pair(
    mps_a, mps_b, support: list[int], cut: int
) -> tuple[np.ndarray, dict]:
    contribution_a, info_a = decision_contribution_from_mps(mps_a, support, cut)
    contribution_b, info_b = decision_contribution_from_mps(mps_b, support, cut)
    operator = contribution_b - contribution_a
    return 0.5 * (operator + operator.conj().T), {
        "a": info_a,
        "b": info_b,
        "total_amplitude_queries": info_a["amplitude_queries"] + info_b["amplitude_queries"],
    }


def spectral_summary(operator: np.ndarray, rank: int) -> dict:
    values = linalg.eigvalsh(operator, check_finite=False)
    values = values[np.argsort(np.abs(values))[::-1]]
    keep = min(max(int(rank), 0), values.size)
    estimate = float(values[:keep].sum(dtype=np.float64))
    tail = float(np.abs(values[keep:]).sum(dtype=np.float64))
    return {
        "rank": keep,
        "estimate": estimate,
        "tail_trace_norm": tail,
        "operator_trace": float(values.sum(dtype=np.float64)),
        "operator_trace_norm": float(np.abs(values).sum(dtype=np.float64)),
        "eigenvalues_by_absolute_value": values,
    }
