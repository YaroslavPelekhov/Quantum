"""Numerical core for the frozen contrastive tensor simulation experiment."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import LinearOperator, eigsh


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
    if isinstance(value, (np.complexfloating, complex)):
        return {"real": float(np.real(value)), "imag": float(np.imag(value))}
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


def canonical_tt_ranks(sites: int, physical: int, max_bond: int) -> list[int]:
    return [1] + [
        min(max_bond, physical ** cut, physical ** (sites - cut))
        for cut in range(1, sites)
    ] + [1]


def canonical_parameter_count(sites: int, physical: int, max_bond: int) -> int:
    ranks = canonical_tt_ranks(sites, physical, max_bond)
    return int(sum(ranks[i] * physical * ranks[i + 1] for i in range(sites)))


def matched_contrast_bond(sites: int, separate_bond: int) -> int:
    budget = 2 * canonical_parameter_count(sites, 2, separate_bond)
    physical_maximum = 2 ** (sites // 2)
    candidate = 1
    while (
        candidate < physical_maximum
        and canonical_parameter_count(sites, 2, candidate + 1) <= budget
    ):
        candidate += 1
    return candidate


def tt_svd_dense(tensor: np.ndarray, max_bond: int) -> tuple[list[np.ndarray], dict]:
    """Deterministic TT-SVD with a hard maximum bond."""

    physical_shape = tensor.shape
    if len(set(physical_shape)) != 1:
        raise ValueError(f"Uniform physical dimensions required: {physical_shape}")
    sites = len(physical_shape)
    physical = physical_shape[0]
    work = np.asarray(tensor).reshape(1, -1)
    cores: list[np.ndarray] = []
    left_rank = 1
    discarded_sq = 0.0
    spectra = []
    for site in range(sites - 1):
        matrix = work.reshape(left_rank * physical, -1)
        u, singular, vh = linalg.svd(
            matrix, full_matrices=False, lapack_driver="gesdd", check_finite=False
        )
        keep = min(max_bond, singular.size)
        discarded_sq += float(np.square(singular[keep:]).sum(dtype=np.float64))
        spectra.append(singular[:keep].copy())
        u = u[:, :keep]
        singular = singular[:keep]
        vh = vh[:keep]
        cores.append(u.reshape(left_rank, physical, keep))
        work = singular[:, None] * vh
        left_rank = keep
    cores.append(work.reshape(left_rank, physical, 1))
    norm_sq = tt_norm_sq(cores)
    return cores, {
        "max_bond": int(max(core.shape[2] for core in cores[:-1]) if sites > 1 else 1),
        "parameter_count": int(sum(core.size for core in cores)),
        "discarded_frobenius_sq_sum": discarded_sq,
        "tt_norm_sq": norm_sq,
        "retained_spectra": spectra,
    }


def tt_norm_sq(cores: list[np.ndarray]) -> float:
    environment = np.ones((1, 1), dtype=np.complex128)
    for core in cores:
        environment = np.einsum(
            "ab,aic,bid->cd", environment, core.conj(), core, optimize=True
        )
    return float(np.real(environment[0, 0]))


def normalize_tt(cores: list[np.ndarray]) -> tuple[list[np.ndarray], float]:
    norm_sq = tt_norm_sq(cores)
    if not np.isfinite(norm_sq) or norm_sq <= 0.0:
        raise AssertionError(f"Invalid TT norm: {norm_sq}")
    result = [np.array(core, copy=True) for core in cores]
    result[0] /= np.sqrt(norm_sq)
    return result, norm_sq


def tt_evaluate_indices(
    cores: list[np.ndarray], indices: list[int] | np.ndarray
) -> np.ndarray:
    indices = np.asarray(indices, dtype=np.int64)
    sites = len(cores)
    values = np.ones((indices.size, 1), dtype=np.result_type(*cores))
    for axis, core in enumerate(cores):
        bit = (indices >> (sites - axis - 1)) & 1
        selected = np.transpose(core[:, bit, :], (1, 0, 2))
        values = np.einsum("ka,kab->kb", values, selected, optimize=True)
    return values[:, 0]


def tt_dense_inner(tensor: np.ndarray, cores: list[np.ndarray]) -> complex:
    environment = np.asarray(tensor).conj()
    first = cores[0][0]
    environment = np.tensordot(first, environment, axes=([0], [0]))
    for core in cores[1:]:
        environment = np.tensordot(core, environment, axes=([0, 1], [0, 1]))
    return complex(np.asarray(environment).reshape(-1)[0])


def tt_reconstruct(cores: list[np.ndarray]) -> np.ndarray:
    result = cores[0][0]
    for core in cores[1:]:
        result = np.tensordot(result, core, axes=([-1], [0]))
    return np.asarray(result[..., 0])


def state_tt_metrics(
    state: np.ndarray, sites: int, bks_indices: list[int], max_bond: int
) -> dict:
    tensor = np.asarray(state).reshape((2,) * sites)
    cores, info = tt_svd_dense(tensor, max_bond)
    overlap = tt_dense_inner(tensor, cores)
    exact_norm = float(np.vdot(state, state).real)
    raw_norm = tt_norm_sq(cores)
    fidelity = float(abs(overlap) ** 2 / (exact_norm * raw_norm))
    normalized, _ = normalize_tt(cores)
    amplitudes = tt_evaluate_indices(normalized, bks_indices)
    probability = float(np.square(np.abs(amplitudes)).sum(dtype=np.float64))
    return {
        "bond": max_bond,
        "probability": probability,
        "fidelity": fidelity,
        "overlap_abs": float(abs(overlap)),
        "raw_norm_sq": raw_norm,
        "parameter_count": info["parameter_count"],
        "actual_max_bond": info["max_bond"],
        "discarded_frobenius_sq_sum": info["discarded_frobenius_sq_sum"],
    }


def signed_tensor_tt_metrics(
    signed_values: np.ndarray, sites: int, bks_indices: list[int], max_bond: int
) -> dict:
    tensor = np.asarray(signed_values).reshape((2,) * sites)
    cores, info = tt_svd_dense(tensor, max_bond)
    values = tt_evaluate_indices(cores, bks_indices)
    return {
        "bond": max_bond,
        "delta": float(np.real(values.sum(dtype=np.complex128))),
        "parameter_count": info["parameter_count"],
        "actual_max_bond": info["max_bond"],
        "tt_norm_sq": info["tt_norm_sq"],
        "discarded_frobenius_sq_sum": info["discarded_frobenius_sq_sum"],
    }


def density_to_operator_tensor(matrix: np.ndarray, sites: int) -> np.ndarray:
    shaped = np.asarray(matrix).reshape((2,) * (2 * sites))
    axes = [axis for pair in zip(range(sites), range(sites, 2 * sites)) for axis in pair]
    return shaped.transpose(axes).reshape((4,) * sites)


def operator_tensor_to_density(tensor: np.ndarray, sites: int) -> np.ndarray:
    shaped = np.asarray(tensor).reshape((2,) * (2 * sites))
    inverse = np.argsort(
        [axis for pair in zip(range(sites), range(sites, 2 * sites)) for axis in pair]
    )
    return shaped.transpose(inverse).reshape(2**sites, 2**sites)


def trace_norm(matrix: np.ndarray) -> float:
    if np.allclose(matrix, matrix.conj().T, atol=1e-11, rtol=1e-11):
        return float(np.abs(linalg.eigvalsh(matrix, check_finite=False)).sum(dtype=np.float64))
    return float(linalg.svdvals(matrix, check_finite=False).sum(dtype=np.float64))


def compress_density_operator(matrix: np.ndarray, sites: int, max_bond: int) -> tuple[np.ndarray, dict]:
    tensor = density_to_operator_tensor(matrix, sites)
    cores, info = tt_svd_dense(tensor, max_bond)
    compressed = operator_tensor_to_density(tt_reconstruct(cores), sites)
    compressed = 0.5 * (compressed + compressed.conj().T)
    residual = trace_norm(matrix - compressed)
    return compressed, {
        "trace_norm_residual": residual,
        "parameter_count": info["parameter_count"],
        "actual_max_bond": info["max_bond"],
        "discarded_frobenius_sq_sum": info["discarded_frobenius_sq_sum"],
    }


def leading_singular_values(
    matrix: np.ndarray, top: int, seed: int = 20260822
) -> np.ndarray:
    rows, columns = matrix.shape
    limit = min(rows, columns)
    if limit <= 256 or top >= limit:
        return linalg.svdvals(matrix, check_finite=False)[:top]
    rank = min(limit, top + 16)
    rng = np.random.default_rng(seed)
    omega = rng.standard_normal((columns, rank))
    if np.iscomplexobj(matrix):
        omega = omega + 1j * rng.standard_normal((columns, rank))
    sample = matrix @ omega
    sample = matrix @ (matrix.conj().T @ sample)
    basis, _ = linalg.qr(sample, mode="economic", check_finite=False)
    reduced = basis.conj().T @ matrix
    singular = linalg.svdvals(reduced, check_finite=False)
    return singular[:top]


def tensor_cut_spectrum(
    values: np.ndarray, sites: int, cut: int, top: int = 64
) -> dict:
    matrix = np.asarray(values).reshape(2**cut, 2 ** (sites - cut))
    singular = leading_singular_values(matrix, top=top, seed=20260822 + cut)
    total_energy = float(np.vdot(values, values).real)
    cumulative = np.cumsum(np.square(singular, dtype=np.float64))
    captured = float(cumulative[-1] / total_energy) if total_energy else 1.0
    effective = next(
        (index + 1 for index, value in enumerate(cumulative) if value >= 0.99 * total_energy),
        None,
    )
    return {
        "cut": cut,
        "leading_singular_values": singular,
        "total_frobenius_energy": total_energy,
        "captured_energy_fraction": captured,
        "effective_rank_99": effective,
        "effective_rank_99_lower_bound": None if effective is not None else len(singular) + 1,
    }


def _kron_gram_matvec(
    left_a: np.ndarray, left_b: np.ndarray, cross: np.ndarray, sign: int, vector: np.ndarray
) -> np.ndarray:
    dimension = left_a.shape[0]
    y = vector.reshape(dimension, dimension, order="F")
    result = left_b.conj() @ y @ left_b.T
    result += left_a.conj() @ y @ left_a.T
    result += sign * (cross.conj() @ y @ cross.T)
    result += sign * (cross.T @ y @ cross.conj())
    return (0.25 * result).reshape(-1, order="F")


def contrastive_operator_spectrum(
    state_a: np.ndarray,
    state_b: np.ndarray,
    sites: int,
    cut: int,
    kind: str,
    top: int = 32,
) -> dict:
    matrix_a = np.asarray(state_a).reshape(2**cut, 2 ** (sites - cut))
    matrix_b = np.asarray(state_b).reshape(2**cut, 2 ** (sites - cut))
    singular_a = linalg.svdvals(matrix_a, check_finite=False)
    singular_b = linalg.svdvals(matrix_b, check_finite=False)
    if kind in {"rho_a", "rho_b"}:
        singular = singular_a if kind == "rho_a" else singular_b
        operator_singular = np.outer(singular, singular).reshape(-1)
        operator_singular.sort()
        operator_singular = operator_singular[::-1]
        total_energy = 1.0
        cumulative = np.cumsum(np.square(operator_singular, dtype=np.float64))
        effective = int(np.searchsorted(cumulative, 0.99 * total_energy) + 1)
        return {
            "kind": kind,
            "cut": cut,
            "leading_singular_values": operator_singular[:top],
            "total_frobenius_energy": total_energy,
            "captured_energy_fraction": float(cumulative[min(top, cumulative.size) - 1]),
            "effective_rank_99": effective,
            "effective_rank_99_lower_bound": None,
        }

    left_a = matrix_a @ matrix_a.conj().T
    left_b = matrix_b @ matrix_b.conj().T
    cross = matrix_b @ matrix_a.conj().T
    overlap_sq = float(abs(np.vdot(state_a, state_b)) ** 2)
    total_energy = 0.5 * (1.0 + overlap_sq) if kind == "mean" else 0.5 * (1.0 - overlap_sq)
    sign = 1 if kind == "mean" else -1
    dimension = left_a.shape[0] ** 2
    count = min(top, dimension - 1) if dimension > 1 else 1
    if dimension <= 4096:
        gram = 0.25 * (
            np.kron(left_b, left_b.conj())
            + np.kron(left_a, left_a.conj())
            + sign * np.kron(cross, cross.conj())
            + sign * np.kron(cross.conj().T, cross.T)
        )
        eigenvalues = linalg.eigvalsh(gram, check_finite=False)
        eigenvalues = np.clip(eigenvalues[::-1], 0.0, None)
    else:
        operator = LinearOperator(
            (dimension, dimension),
            matvec=lambda vector: _kron_gram_matvec(
                left_a, left_b, cross, sign, vector
            ),
            dtype=np.complex128,
        )
        eigenvalues = eigsh(
            operator, k=count, which="LA", return_eigenvectors=False, tol=1e-9
        )
        eigenvalues = np.clip(np.sort(eigenvalues)[::-1], 0.0, None)
    singular = np.sqrt(eigenvalues[:top])
    cumulative = np.cumsum(eigenvalues[:top])
    effective = next(
        (index + 1 for index, value in enumerate(cumulative) if value >= 0.99 * total_energy),
        None,
    )
    return {
        "kind": kind,
        "cut": cut,
        "leading_singular_values": singular,
        "total_frobenius_energy": total_energy,
        "captured_energy_fraction": float(cumulative[-1] / total_energy) if total_energy else 1.0,
        "effective_rank_99": effective,
        "effective_rank_99_lower_bound": None if effective is not None else len(singular) + 1,
    }
