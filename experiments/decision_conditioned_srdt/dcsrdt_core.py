"""Decision-conditioned signed reduced-density truncation primitives."""

from __future__ import annotations

import numpy as np
from scipy import linalg


def trace_norm_hermitian(matrix: np.ndarray) -> float:
    values = linalg.eigvalsh(matrix, check_finite=False)
    return float(np.abs(values).sum(dtype=np.float64))


def reduced_density(state: np.ndarray, cut: int) -> np.ndarray:
    sites = int(round(np.log2(state.size)))
    if state.ndim != 1 or (1 << sites) != state.size or not 0 < cut < sites:
        raise ValueError("Invalid state or cut")
    matrix = np.asarray(state).reshape(1 << cut, -1)
    return matrix @ matrix.conj().T


def decision_conditioned_operator(
    state_a: np.ndarray,
    state_b: np.ndarray,
    effect_diagonal: np.ndarray,
    cut: int,
) -> np.ndarray:
    """Return Tr_R({E, |B><B|-|A><A|}/2) for diagonal E."""
    if state_a.shape != state_b.shape or state_a.ndim != 1:
        raise ValueError("Expected equally sized statevectors")
    if effect_diagonal.shape != state_a.shape:
        raise ValueError("Effect diagonal must match the state dimension")
    if np.any(effect_diagonal < 0.0) or np.any(effect_diagonal > 1.0):
        raise ValueError("Effect must satisfy 0 <= E <= I")
    left = 1 << cut
    a = np.asarray(state_a).reshape(left, -1)
    b = np.asarray(state_b).reshape(left, -1)
    effect = np.asarray(effect_diagonal, dtype=np.float64).reshape(left, -1)

    def contribution(state: np.ndarray) -> np.ndarray:
        weighted = effect * state
        raw = weighted @ state.conj().T
        return 0.5 * (raw + raw.conj().T)

    result = contribution(b) - contribution(a)
    return 0.5 * (result + result.conj().T)


def absolute_eigenbasis(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = linalg.eigh(matrix, check_finite=False)
    order = np.argsort(np.abs(values))[::-1]
    return values[order], vectors[:, order]


def positive_eigenbasis(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = linalg.eigh(matrix, check_finite=False)
    order = np.argsort(values)[::-1]
    return values[order], vectors[:, order]


def projected_operator(matrix: np.ndarray, basis: np.ndarray, rank: int) -> np.ndarray:
    keep = min(max(int(rank), 0), basis.shape[1])
    selected = basis[:, :keep]
    projector = selected @ selected.conj().T
    return projector @ matrix @ projector


def bks_effect_diagonal(scorer: dict) -> np.ndarray:
    """Vectorized exact BKS indicator in Qiskit's integer basis order."""
    qubits = len(scorer["weights"])
    indices = np.arange(1 << qubits, dtype=np.uint32)
    selected = np.full(indices.size, scorer["constant_selected"], dtype=np.int16)
    for qubit, weight in enumerate(scorer["weights"]):
        if weight:
            selected += np.int16(weight) * ((indices >> qubit) & 1).astype(np.int16)
    feasible = np.full(indices.size, not scorer["impossible"], dtype=bool)
    for mask, pattern in scorer["forbidden"]:
        feasible &= (indices & np.uint32(mask)) != np.uint32(pattern)
    return (feasible & (selected >= scorer["bks"])).astype(np.float64)


def benchmark_pair(
    state_a: np.ndarray,
    state_b: np.ndarray,
    effect_diagonal: np.ndarray,
    cut: int,
    ranks: tuple[int, ...],
) -> dict:
    rho_a = reduced_density(state_a, cut)
    rho_b = reduced_density(state_b, cut)
    gamma_local = 0.5 * ((rho_b - rho_a) + (rho_b - rho_a).conj().T)
    rho_average = 0.5 * (rho_a + rho_b)
    decision = decision_conditioned_operator(state_a, state_b, effect_diagonal, cut)
    exact_delta = float(
        np.sum(effect_diagonal * (np.abs(state_b) ** 2 - np.abs(state_a) ** 2))
    )
    decision_values, decision_basis = absolute_eigenbasis(decision)
    _, signed_basis = absolute_eigenbasis(gamma_local)
    _, average_basis = positive_eigenbasis(rho_average)
    methods = {
        "decision_conditioned": decision_basis,
        "srdt_basis": signed_basis,
        "state_averaged_basis": average_basis,
    }
    rows = []
    for rank in ranks:
        row = {"rank": int(rank), "methods": {}}
        for name, basis in methods.items():
            approximation = projected_operator(decision, basis, rank)
            residual = decision - approximation
            estimate = float(np.trace(approximation).real)
            bound = trace_norm_hermitian(residual)
            row["methods"][name] = {
                "estimate": estimate,
                "absolute_error": abs(estimate - exact_delta),
                "trace_norm_bound": bound,
                "sign_correct": bool(np.sign(estimate) == np.sign(exact_delta)),
                "sign_certified": bool(abs(estimate) > bound),
            }
        target = row["methods"]["decision_conditioned"]
        target["spectral_tail"] = float(
            np.abs(decision_values[min(rank, decision_values.size):]).sum(dtype=np.float64)
        )
        rows.append(row)
    return {
        "cut": cut,
        "left_dimension": decision.shape[0],
        "exact_delta": exact_delta,
        "operator_trace": float(np.trace(decision).real),
        "operator_hermiticity_error": float(np.linalg.norm(decision - decision.conj().T)),
        "decision_trace_norm": trace_norm_hermitian(decision),
        "rows": rows,
    }
