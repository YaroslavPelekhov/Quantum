"""Core inequalities and dense-oracle TT-SVD for Certified Observable Telescope."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np


TOKEN_RE = re.compile(r"I(?P<instruction>[0-9]+):|internal_swap on qubits")
VALUE_RE = re.compile(r"discarded_value=([0-9.eE+-]+)")


def robust_svd(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Use the fast SVD driver, with conservative QR-iteration fallback."""
    if not np.all(np.isfinite(matrix)):
        raise FloatingPointError("Non-finite TT-SVD input")
    try:
        return np.linalg.svd(matrix, full_matrices=False)
    except np.linalg.LinAlgError:
        from scipy.linalg import svd

        return svd(
            matrix,
            full_matrices=False,
            check_finite=False,
            lapack_driver="gesvd",
        )


def printed_double_upper_bound(text: str) -> float:
    """Upper endpoint of the decimal rounding bin used by Aer MPS logs."""
    value = float(text)
    if value == 0.0:
        return 0.0
    mantissa = text.lower().split("e", 1)[0].lstrip("+-").replace(".", "").lstrip("0")
    significant_digits = len(mantissa)
    exponent = int(text.lower().split("e", 1)[1]) if "e" in text.lower() else 0
    decimal_places = len(text.split("e", 1)[0].split(".", 1)[1]) if "." in text.split("e", 1)[0] else 0
    quantum = 10.0 ** (exponent - decimal_places)
    # The significant-digit count is retained as a defensive format check.
    if significant_digits == 0:
        return 0.0
    return math.nextafter(value + 0.5 * quantum, math.inf)


def group_aer_weights_by_instruction(raw_log: str) -> dict[int, list[float]]:
    """Assign internal-swap truncations preceding I<n> to instruction n.

    Aer logs internal swaps before the I<n> marker for the logical non-local
    two-qubit instruction. A discarded value on I<n> itself belongs to the same
    instruction. The returned values are upper rounding-bin endpoints.
    """
    matches = list(TOKEN_RE.finditer(raw_log))
    assigned: list[list[float]] = [[] for _ in matches]
    for value_match in VALUE_RE.finditer(raw_log):
        context = next(
            (index for index, token in enumerate(matches) if token.start() > value_match.start()),
            None,
        )
        if context is None:
            raise AssertionError("Aer discarded value has no following operation token")
        assigned[context].append(printed_double_upper_bound(value_match.group(1)))
    pending: list[float] = []
    groups: dict[int, list[float]] = {}
    for position, match in enumerate(matches):
        values = assigned[position]
        instruction = match.group("instruction")
        if instruction is None:
            pending.extend(values)
            continue
        index = int(instruction)
        if index in groups:
            raise AssertionError(f"Duplicate Aer instruction marker I{index}")
        groups[index] = pending + values
        pending = []
    if pending:
        raise AssertionError("Unassigned internal-swap truncations after final instruction")
    if sorted(groups) != list(range(len(groups))):
        raise AssertionError("Aer instruction markers are not contiguous")
    return groups


def grouped_angle_and_effective_weight(weights: list[float]) -> tuple[float, float, float]:
    angle = min(
        math.pi / 2,
        math.fsum(math.asin(math.sqrt(min(1.0, max(0.0, weight)))) for weight in weights),
    )
    effective_weight = math.sin(angle) ** 2
    return angle, effective_weight, 2.0 * math.sqrt(effective_weight)


def compress_statevector_ttsvd(state: np.ndarray, max_bond: int) -> tuple[np.ndarray, dict]:
    """Normalize a TT-SVD approximation with every TT rank <= max_bond."""
    vector = np.asarray(state, dtype=np.complex128)
    qubits_float = math.log2(vector.size)
    qubits = int(round(qubits_float))
    if 1 << qubits != vector.size:
        raise ValueError("State dimension is not a power of two")
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("Invalid state norm")
    vector = vector / norm
    exact_max_bond = 1 << (qubits // 2)
    if max_bond >= exact_max_bond:
        return vector.copy(), {
            "compression_angle": 0.0,
            "compression_angle_from_residual": 0.0,
            "phase_aligned_norm_error": 0.0,
            "overlap": 1.0,
            "max_retained_rank": exact_max_bond,
            "sum_local_discarded_squared": 0.0,
        }
    remainder = vector.reshape((2,) * qubits, order="F")
    left_rank = 1
    cores = []
    discarded_squared = []
    retained_ranks = []
    for _site in range(qubits - 1):
        matrix = remainder.reshape(left_rank * 2, -1)
        u, singular, vh = robust_svd(matrix)
        keep = min(max_bond, singular.size)
        discarded_squared.append(float(np.sum(np.square(singular[keep:]))))
        retained_ranks.append(keep)
        cores.append(u[:, :keep].reshape(left_rank, 2, keep))
        remainder = singular[:keep, None] * vh[:keep, :]
        left_rank = keep
    cores.append(remainder.reshape(left_rank, 2, 1))
    reconstructed = cores[0]
    for core in cores[1:]:
        reconstructed = np.tensordot(reconstructed, core, axes=([-1], [0]))
    approximation = reconstructed.reshape(-1, order="F")
    approximation /= np.linalg.norm(approximation)
    complex_overlap = np.vdot(vector, approximation)
    if abs(complex_overlap) > 0:
        approximation *= np.exp(-1j * np.angle(complex_overlap))
    overlap = min(1.0, max(0.0, float(abs(np.vdot(vector, approximation)))))
    angle = math.acos(overlap)
    phase_aligned_norm_error = float(np.linalg.norm(vector - approximation))
    residual_angle = 2.0 * math.asin(min(1.0, phase_aligned_norm_error / 2.0))
    return approximation, {
        "compression_angle": angle,
        "compression_angle_from_residual": residual_angle,
        "phase_aligned_norm_error": phase_aligned_norm_error,
        "overlap": overlap,
        "max_retained_rank": max(retained_ranks, default=1),
        "sum_local_discarded_squared": math.fsum(discarded_squared),
    }


def compress_vector_ttsvd_unnormalized(
    vector: np.ndarray, max_bond: int
) -> tuple[np.ndarray, dict]:
    """TT-SVD an arbitrary vector without changing its norm or phase.

    The returned ``discarded_norm_upper_bound`` is the standard TT-SVD
    Frobenius/Euclidean error bound sqrt(sum_k epsilon_k^2), where epsilon_k
    is the discarded singular-value tail at split k.  Unlike
    :func:`compress_statevector_ttsvd`, this routine deliberately performs no
    normalization or phase alignment, so it can be used inside a linear
    residual recurrence.
    """
    value = np.asarray(vector, dtype=np.complex128)
    qubits_float = math.log2(value.size)
    qubits = int(round(qubits_float))
    if 1 << qubits != value.size:
        raise ValueError("Vector dimension is not a power of two")
    norm = float(np.linalg.norm(value))
    if not np.isfinite(norm):
        raise ValueError("Invalid vector norm")
    if norm == 0.0:
        return np.zeros_like(value), {
            "discarded_norm_upper_bound": 0.0,
            "sum_local_discarded_squared": 0.0,
            "max_retained_rank": 1,
            "input_norm": 0.0,
        }
    exact_max_bond = 1 << (qubits // 2)
    if max_bond >= exact_max_bond:
        return value.copy(), {
            "discarded_norm_upper_bound": 0.0,
            "sum_local_discarded_squared": 0.0,
            "max_retained_rank": exact_max_bond,
            "input_norm": norm,
        }
    # TT-SVD is homogeneous.  Unit scaling avoids LAPACK non-convergence on
    # residuals whose norms are close to the subnormal/roundoff regime.
    remainder = (value / norm).reshape((2,) * qubits, order="F")
    left_rank = 1
    cores = []
    discarded_squared = []
    retained_ranks = []
    for _site in range(qubits - 1):
        matrix = remainder.reshape(left_rank * 2, -1)
        u, singular, vh = robust_svd(matrix)
        keep = min(max_bond, singular.size)
        discarded_squared.append(float(np.sum(np.square(singular[keep:]))))
        retained_ranks.append(keep)
        cores.append(u[:, :keep].reshape(left_rank, 2, keep))
        remainder = singular[:keep, None] * vh[:keep, :]
        left_rank = keep
    cores.append(remainder.reshape(left_rank, 2, 1))
    reconstructed = cores[0]
    for core in cores[1:]:
        reconstructed = np.tensordot(reconstructed, core, axes=([-1], [0]))
    approximation = reconstructed.reshape(-1, order="F") * norm
    discarded_sum = math.fsum(discarded_squared) * norm * norm
    return approximation, {
        "discarded_norm_upper_bound": math.sqrt(max(0.0, discarded_sum)),
        "sum_local_discarded_squared": discarded_sum,
        "max_retained_rank": max(retained_ranks, default=1),
        "input_norm": norm,
    }


def projector_operator_norm_difference(exact: np.ndarray, approximate: np.ndarray) -> float:
    """Exact norm of VV^dagger-WW^dagger through its <=2r dimensional span."""
    basis = np.concatenate([exact, approximate], axis=1)
    q, _ = np.linalg.qr(basis)
    reduced_exact = q.conj().T @ exact
    reduced_approximate = q.conj().T @ approximate
    reduced = (
        reduced_exact @ reduced_exact.conj().T
        - reduced_approximate @ reduced_approximate.conj().T
    )
    return float(np.max(np.abs(np.linalg.eigvalsh(reduced))))


def terminal_basis_vectors(qubits: int, indices: list[int]) -> np.ndarray:
    vectors = np.zeros((1 << qubits, len(indices)), dtype=np.complex128)
    for column, index in enumerate(indices):
        vectors[index, column] = 1.0
    return vectors
