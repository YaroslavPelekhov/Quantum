"""Core routines for signed reduced-density truncation (SRDT)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from scipy import linalg


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(jsonable(payload), handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def trace_norm_hermitian(matrix: np.ndarray) -> float:
    values = linalg.eigvalsh(matrix, check_finite=False)
    return float(np.abs(values).sum(dtype=np.float64))


def reduced_pair(state_a: np.ndarray, state_b: np.ndarray, cut: int) -> tuple[np.ndarray, np.ndarray]:
    """Return left reduced density matrices at a qubit cut."""
    if state_a.shape != state_b.shape or state_a.ndim != 1:
        raise ValueError("Expected equally sized statevectors")
    sites = int(round(np.log2(state_a.size)))
    if (1 << sites) != state_a.size or not 0 < cut < sites:
        raise ValueError("Invalid state dimension or cut")
    matrix_a = np.asarray(state_a).reshape(1 << cut, -1)
    matrix_b = np.asarray(state_b).reshape(1 << cut, -1)
    return matrix_a @ matrix_a.conj().T, matrix_b @ matrix_b.conj().T


def truncate_hermitian_absolute(matrix: np.ndarray, rank: int) -> tuple[np.ndarray, dict]:
    """Best rank-k Hermitian approximation in every Schatten p norm.

    Eigenpairs are ordered by absolute eigenvalue, not algebraic value.
    For p=1 the exact residual is the sum of the discarded absolute values.
    """
    values, vectors = linalg.eigh(matrix, check_finite=False)
    order = np.argsort(np.abs(values))[::-1]
    values = values[order]
    vectors = vectors[:, order]
    keep = min(max(0, int(rank)), values.size)
    retained = vectors[:, :keep] @ np.diag(values[:keep]) @ vectors[:, :keep].conj().T
    tail = float(np.abs(values[keep:]).sum(dtype=np.float64))
    return retained, {
        "rank": keep,
        "eigenvalues_by_absolute_value": values,
        "trace_norm": float(np.abs(values).sum(dtype=np.float64)),
        "tail_trace_norm": tail,
    }


def state_averaged_projection(
    gamma: np.ndarray, rho_average: np.ndarray, rank: int
) -> tuple[np.ndarray, dict]:
    """Project Gamma into the conventional state-averaged DMRG subspace."""
    values, vectors = linalg.eigh(rho_average, check_finite=False)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    keep = min(max(0, int(rank)), values.size)
    basis = vectors[:, :keep]
    projector = basis @ basis.conj().T
    approximation = projector @ gamma @ projector
    residual = trace_norm_hermitian(gamma - approximation)
    return approximation, {
        "rank": keep,
        "retained_average_mass": float(values[:keep].sum(dtype=np.float64)),
        "tail_average_mass": float(values[keep:].sum(dtype=np.float64)),
        "contrast_trace_norm_error": residual,
    }


def cut_benchmark(
    state_a: np.ndarray, state_b: np.ndarray, cut: int, ranks: tuple[int, ...]
) -> dict:
    rho_a, rho_b = reduced_pair(state_a, state_b, cut)
    gamma = 0.5 * ((rho_b - rho_a) + (rho_b - rho_a).conj().T)
    rho_average = 0.5 * (rho_a + rho_b)
    gamma_norm = trace_norm_hermitian(gamma)
    rows = []
    for rank in ranks:
        if rank > gamma.shape[0]:
            continue
        _, signed = truncate_hermitian_absolute(gamma, rank)
        _, averaged = state_averaged_projection(gamma, rho_average, rank)
        rows.append({
            "rank": rank,
            "signed_optimal_error": signed["tail_trace_norm"],
            "signed_relative_error": signed["tail_trace_norm"] / gamma_norm if gamma_norm else 0.0,
            "state_averaged_contrast_error": averaged["contrast_trace_norm_error"],
            "state_averaged_relative_error": averaged["contrast_trace_norm_error"] / gamma_norm if gamma_norm else 0.0,
            "state_averaged_tail_mass": averaged["tail_average_mass"],
            "improvement_factor": (
                averaged["contrast_trace_norm_error"] / signed["tail_trace_norm"]
                if signed["tail_trace_norm"] > 1e-15 else None
            ),
        })
    return {
        "cut": cut,
        "left_dimension": gamma.shape[0],
        "contrast_trace_norm": gamma_norm,
        "rows": rows,
    }


def synthetic_pair(local_qubits: int, epsilon: float = 0.1) -> tuple[np.ndarray, np.ndarray]:
    """Pure-state family with hard states and a rank-two local contrast.

    The two halves each have dimension D=2**local_qubits.  D-2 Schmidt
    components form an identical maximally entangled common mode.  The last
    component of each branch occupies a different Schmidt basis vector.
    """
    dimension = 1 << local_qubits
    if dimension < 4 or not 0.0 < epsilon < 1.0:
        raise ValueError("Need local_qubits >= 2 and 0 < epsilon < 1")
    common = dimension - 2
    state_a = np.zeros(dimension * dimension, dtype=np.complex128)
    state_b = np.zeros_like(state_a)
    common_amplitude = np.sqrt((1.0 - epsilon) / common)
    for index in range(common):
        state_a[index * dimension + index] = common_amplitude
        state_b[index * dimension + index] = common_amplitude
    state_a[(dimension - 2) * dimension + (dimension - 2)] = np.sqrt(epsilon)
    state_b[(dimension - 1) * dimension + (dimension - 1)] = np.sqrt(epsilon)
    return state_a, state_b


def rank_for_fidelity(rho: np.ndarray, target: float) -> int:
    values = linalg.eigvalsh(rho, check_finite=False)[::-1]
    return int(np.searchsorted(np.cumsum(values), target, side="left") + 1)


def synthetic_metrics(local_qubits: int, epsilon: float = 0.1, fidelity: float = 0.99) -> dict:
    state_a, state_b = synthetic_pair(local_qubits, epsilon)
    rho_a, rho_b = reduced_pair(state_a, state_b, local_qubits)
    gamma = rho_b - rho_a
    gamma_values = linalg.eigvalsh(gamma, check_finite=False)
    nonzero = int(np.count_nonzero(np.abs(gamma_values) > 1e-12))
    rank_a = rank_for_fidelity(rho_a, fidelity)
    rank_b = rank_for_fidelity(rho_b, fidelity)
    contrast_observable = np.zeros_like(gamma)
    contrast_observable[-1, -1] = 1.0
    contrast_observable[-2, -2] = -1.0
    delta = float(np.trace(contrast_observable @ gamma).real)
    return {
        "local_qubits": local_qubits,
        "total_qubits": 2 * local_qubits,
        "local_dimension": 1 << local_qubits,
        "epsilon": epsilon,
        "fidelity_target": fidelity,
        "state_a_required_schmidt_rank": rank_a,
        "state_b_required_schmidt_rank": rank_b,
        "contrast_exact_rank": nonzero,
        "state_to_contrast_rank_ratio": min(rank_a, rank_b) / nonzero,
        "contrast_trace_norm": trace_norm_hermitian(gamma),
        "witness_delta": delta,
    }
