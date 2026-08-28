"""Dense oracle for contrast-augmented common-subspace evolution."""

from __future__ import annotations

import numpy as np
from qiskit.quantum_info import Statevector
from scipy import linalg


def absolute_hermitian(matrix: np.ndarray) -> np.ndarray:
    values, vectors = linalg.eigh(matrix, check_finite=False)
    return (vectors * np.abs(values)) @ vectors.conj().T


def common_project_pair(
    state_a: np.ndarray,
    state_b: np.ndarray,
    sites: int,
    cut: int,
    rank: int,
    alpha: float,
) -> tuple[np.ndarray, np.ndarray, dict]:
    left = 1 << cut
    matrix_a = np.asarray(state_a).reshape(left, -1)
    matrix_b = np.asarray(state_b).reshape(left, -1)
    rho_a = matrix_a @ matrix_a.conj().T
    rho_b = matrix_b @ matrix_b.conj().T
    average = 0.5 * (rho_a + rho_b)
    gamma = 0.5 * ((rho_b - rho_a) + (rho_b - rho_a).conj().T)
    target = average + alpha * absolute_hermitian(gamma)
    values, vectors = linalg.eigh(target, check_finite=False)
    keep = min(rank, left)
    basis = vectors[:, np.argsort(values)[::-1][:keep]]
    projected_a = (basis @ (basis.conj().T @ matrix_a)).reshape(-1)
    projected_b = (basis @ (basis.conj().T @ matrix_b)).reshape(-1)
    norm_a = float(np.linalg.norm(projected_a))
    norm_b = float(np.linalg.norm(projected_b))
    if norm_a <= 1e-14 or norm_b <= 1e-14:
        raise FloatingPointError("Projection annihilated a branch")
    return projected_a / norm_a, projected_b / norm_b, {
        "retained_norm_a": norm_a,
        "retained_norm_b": norm_b,
    }


def evolve_operation(state: np.ndarray, operation, qargs: tuple[int, ...]) -> np.ndarray:
    return np.asarray(Statevector(state).evolve(operation, qargs=list(qargs)).data)


def run_pair(circuit_a, circuit_b, cut: int, rank: int, alpha: float) -> tuple[np.ndarray, np.ndarray, dict]:
    sites = circuit_a.num_qubits
    if sites != circuit_b.num_qubits or len(circuit_a.data) != len(circuit_b.data):
        raise ValueError("Paired circuit shapes differ")
    state_a = np.zeros(1 << sites, dtype=np.complex128)
    state_b = np.zeros_like(state_a)
    state_a[0] = state_b[0] = 1.0
    minimum_retained = 1.0
    for item_a, item_b in zip(circuit_a.data, circuit_b.data):
        qargs_a = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        qargs_b = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
        state_a = evolve_operation(state_a, item_a.operation, qargs_a)
        state_b = evolve_operation(state_b, item_b.operation, qargs_b)
        state_a, state_b, info = common_project_pair(
            state_a, state_b, sites, cut, rank, alpha
        )
        minimum_retained = min(
            minimum_retained, info["retained_norm_a"], info["retained_norm_b"]
        )
    return state_a, state_b, {
        "paired_gates": len(circuit_a.data),
        "minimum_retained_norm": minimum_retained,
    }
