"""Incremental real Lie-closure calculation for small Hermitian generators."""

from __future__ import annotations

import numpy as np


def _traceless_skew(hamiltonian: np.ndarray) -> np.ndarray:
    dimension = hamiltonian.shape[0]
    traceless = hamiltonian - np.trace(hamiltonian) * np.eye(dimension) / dimension
    return 1j * traceless


def _real_vector(matrix: np.ndarray) -> np.ndarray:
    return np.concatenate((matrix.real.reshape(-1), matrix.imag.reshape(-1)))


def lie_dimension(hermitian_generators: list[np.ndarray], tolerance: float = 1e-9) -> int:
    """Return the dimension of the generated traceless skew-Hermitian Lie algebra."""
    if not hermitian_generators:
        return 0
    dimension = hermitian_generators[0].shape[0]
    target = dimension * dimension - 1
    matrices: list[np.ndarray] = []
    vectors: list[np.ndarray] = []
    pending: list[tuple[np.ndarray, int]] = []

    def add(candidate: np.ndarray) -> bool:
        vector = _real_vector(candidate)
        if vectors:
            basis = np.stack(vectors)
            vector = vector - basis.T @ (basis @ vector)
            vector = vector - basis.T @ (basis @ vector)
        norm = float(np.linalg.norm(vector))
        if norm <= tolerance:
            return False
        normalized_matrix = candidate
        if vectors:
            # Reconstruct the matrix residual so commutators use the same orthogonal direction.
            residual = vector[: dimension * dimension].reshape(dimension, dimension) + 1j * vector[
                dimension * dimension :
            ].reshape(dimension, dimension)
            normalized_matrix = residual
        normalized_matrix = normalized_matrix / norm
        normalized_vector = _real_vector(normalized_matrix)
        # Final normalization protects against roundoff in the reconstruction.
        normalized_vector /= np.linalg.norm(normalized_vector)
        normalized_matrix = normalized_vector[: dimension * dimension].reshape(dimension, dimension) + 1j * normalized_vector[
            dimension * dimension :
        ].reshape(dimension, dimension)
        old_count = len(matrices)
        matrices.append(normalized_matrix)
        vectors.append(normalized_vector)
        pending.append((normalized_matrix, old_count))
        return True

    for generator in hermitian_generators:
        add(_traceless_skew(np.asarray(generator, dtype=complex)))

    cursor = 0
    while cursor < len(pending) and len(matrices) < target:
        newest, previous_count = pending[cursor]
        cursor += 1
        for other in matrices[:previous_count]:
            commutator = newest @ other - other @ newest
            add(commutator)
            if len(matrices) >= target:
                break
    return len(matrices)


def control_generators(model, spatial_mode: str) -> list[np.ndarray]:
    generators = [model.interaction, model.x_sum, model.y_sum, model.number]
    if spatial_mode == "gradient_mask":
        generators.append(model.mask_number)
    elif spatial_mode not in {"global_only", "uniform_mask"}:
        raise ValueError(f"unknown spatial_mode: {spatial_mode}")
    return generators

