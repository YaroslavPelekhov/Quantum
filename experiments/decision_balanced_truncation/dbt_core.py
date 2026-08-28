"""Dense oracle core for decision-balanced Petrov--Galerkin truncation."""

from __future__ import annotations

import numpy as np
from qiskit.quantum_info import Operator
from scipy import linalg


def apply_gate_batch(
    states: np.ndarray, operation, qargs: tuple[int, ...], sites: int, inverse: bool = False
) -> np.ndarray:
    """Apply a one/two-qubit Qiskit operation to columns of statevectors."""
    values = np.asarray(states)
    vector_input = values.ndim == 1
    if vector_input:
        values = values[:, None]
    if values.shape[0] != 1 << sites:
        raise ValueError("State dimension does not match sites")
    unitary = np.asarray(Operator(operation).data)
    if inverse:
        unitary = unitary.conj().T
    target_axes = [sites - 1 - qubit for qubit in reversed(qargs)]
    other_axes = [axis for axis in range(sites) if axis not in target_axes]
    permutation = target_axes + other_axes + [sites]
    tensor = values.reshape((2,) * sites + (values.shape[1],))
    moved = tensor.transpose(permutation)
    target_dimension = 1 << len(qargs)
    flat = moved.reshape(target_dimension, -1)
    flat = unitary @ flat
    restored = flat.reshape(moved.shape)
    inverse_permutation = np.argsort(permutation)
    result = restored.transpose(inverse_permutation).reshape(values.shape)
    return result[:, 0] if vector_input else result


def reduced_gram(states: np.ndarray, cut: int) -> np.ndarray:
    values = np.asarray(states)
    if values.ndim == 1:
        values = values[:, None]
    left = 1 << cut
    matrix = values.reshape(left, -1, values.shape[1])
    return np.einsum("arb,crb->ac", matrix, matrix.conj(), optimize=True)


def psd_square_root(matrix: np.ndarray) -> np.ndarray:
    values, vectors = linalg.eigh(0.5 * (matrix + matrix.conj().T), check_finite=False)
    return (vectors * np.sqrt(np.clip(values, 0.0, None))) @ vectors.conj().T


def state_averaged_projector(reachability: np.ndarray, rank: int) -> np.ndarray:
    values, vectors = linalg.eigh(reachability, check_finite=False)
    basis = vectors[:, np.argsort(values)[::-1][:rank]]
    return basis @ basis.conj().T


def balanced_projector(reachability: np.ndarray, observability: np.ndarray, rank: int) -> tuple[np.ndarray, dict]:
    x = psd_square_root(reachability)
    y = psd_square_root(observability)
    u, singular, vh = linalg.svd(y.conj().T @ x, full_matrices=False, check_finite=False)
    nonzero = int(np.count_nonzero(singular > 1e-12))
    keep = min(rank, nonzero)
    if keep < rank:
        return state_averaged_projector(reachability, rank), {
            "fallback": True,
            "hankel_singular_values": singular,
            "biorthogonality_error": 0.0,
        }
    scale = 1.0 / np.sqrt(singular[:keep])
    trial = (x @ vh.conj().T[:, :keep]) * scale
    test = (y @ u[:, :keep]) * scale
    biorthogonality = float(np.linalg.norm(test.conj().T @ trial - np.eye(keep)))
    return trial @ test.conj().T, {
        "fallback": False,
        "hankel_singular_values": singular,
        "biorthogonality_error": biorthogonality,
    }


def hankel_singular_values(reachability: np.ndarray, observability: np.ndarray) -> np.ndarray:
    x = psd_square_root(reachability)
    y = psd_square_root(observability)
    return linalg.svdvals(y.conj().T @ x, check_finite=False)


def select_hankel_rank(
    singular: np.ndarray,
    allowed: tuple[int, ...] = (1, 2, 4, 8),
    energy_fraction: float = 0.99,
) -> int:
    energy = np.square(np.asarray(singular), dtype=np.float64)
    total = float(energy.sum(dtype=np.float64))
    if total <= 1e-28:
        return allowed[0]
    required = int(np.searchsorted(np.cumsum(energy), energy_fraction * total) + 1)
    return next((rank for rank in allowed if rank >= required), allowed[-1])


def apply_left_projector(states: np.ndarray, projector: np.ndarray, cut: int) -> np.ndarray:
    values = np.asarray(states)
    vector_input = values.ndim == 1
    if vector_input:
        values = values[:, None]
    left = 1 << cut
    matrix = values.reshape(left, -1, values.shape[1])
    projected = np.einsum("ac,crb->arb", projector, matrix, optimize=True).reshape(values.shape)
    norms = np.linalg.norm(projected, axis=0)
    if np.any(norms <= 1e-14):
        raise FloatingPointError("Projection annihilated a state")
    projected = projected / norms[None, :]
    return projected[:, 0] if vector_input else projected


def backward_observability(circuit, indices: list[int], cut: int) -> list[np.ndarray]:
    sites = circuit.num_qubits
    vectors = np.zeros((1 << sites, len(indices)), dtype=np.complex128)
    vectors[np.asarray(indices), np.arange(len(indices))] = 1.0
    output: list[np.ndarray] = [None] * len(circuit.data)  # type: ignore[list-item]
    for position in range(len(circuit.data) - 1, -1, -1):
        output[position] = reduced_gram(vectors, cut)
        item = circuit.data[position]
        qargs = tuple(circuit.find_bit(qubit).index for qubit in item.qubits)
        vectors = apply_gate_batch(vectors, item.operation, qargs, sites, inverse=True)
    return output


def evolve_reduced_pair(
    circuit_a,
    circuit_b,
    indices: list[int],
    cut: int,
    rank: int,
    method: str,
) -> tuple[np.ndarray, dict]:
    if method not in {"state_averaged", "decision_balanced"}:
        raise ValueError(method)
    sites = circuit_a.num_qubits
    if sites != circuit_b.num_qubits or len(circuit_a.data) != len(circuit_b.data):
        raise ValueError("Paired circuit shapes differ")
    obs_a = backward_observability(circuit_a, indices, cut) if method == "decision_balanced" else None
    obs_b = backward_observability(circuit_b, indices, cut) if method == "decision_balanced" else None
    states = np.zeros((1 << sites, 2), dtype=np.complex128)
    states[0, :] = 1.0
    max_biorthogonality = 0.0
    fallbacks = 0
    for position, (item_a, item_b) in enumerate(zip(circuit_a.data, circuit_b.data)):
        qargs_a = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        qargs_b = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
        states[:, 0] = apply_gate_batch(states[:, 0], item_a.operation, qargs_a, sites)
        states[:, 1] = apply_gate_batch(states[:, 1], item_b.operation, qargs_b, sites)
        reachability = 0.5 * reduced_gram(states, cut)
        if method == "state_averaged":
            projector = state_averaged_projector(reachability, rank)
        else:
            observability = 0.5 * (obs_a[position] + obs_b[position]) / len(indices)
            projector, info = balanced_projector(reachability, observability, rank)
            max_biorthogonality = max(max_biorthogonality, info["biorthogonality_error"])
            fallbacks += int(info["fallback"])
        states = apply_left_projector(states, projector, cut)
    return states, {
        "paired_gates": len(circuit_a.data),
        "max_biorthogonality_error": max_biorthogonality,
        "fallback_count": fallbacks,
    }
