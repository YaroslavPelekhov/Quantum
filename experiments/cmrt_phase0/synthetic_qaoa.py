"""Small, deterministic QAOA-MIS simulator used by the CMRT Phase-0 screen.

The module deliberately depends only on NumPy.  Basis indices use the usual
little-endian convention: qubit ``q`` is bit ``(index >> q) & 1``.  A qubit
order therefore affects only the tensor-train truncation, never the meaning of
an output bitstring.

The MIS cost Hamiltonian is

    H_C(x) = -sum_i x_i + penalty * sum_(u,v) w_(u,v) x_u x_v,

so lower energy favours large independent sets when ``penalty`` is large
enough.  Each QAOA layer applies ``exp(-i gamma H_C)`` followed by independent
``exp(-i beta X)`` mixers.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import numpy as np


Array = np.ndarray
Event = Iterable[int | str] | Array | Callable[[int], bool]


def _validate_problem(
    n_qubits: int,
    edges: Iterable[tuple[int, int]],
    edge_weights: Sequence[float] | Array | None = None,
) -> tuple[tuple[tuple[int, int], ...], Array]:
    if not isinstance(n_qubits, (int, np.integer)) or int(n_qubits) < 1:
        raise ValueError("n_qubits must be a positive integer")
    n_qubits = int(n_qubits)

    clean_edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for raw_u, raw_v in edges:
        u, v = int(raw_u), int(raw_v)
        if not (0 <= u < n_qubits and 0 <= v < n_qubits):
            raise ValueError(f"edge {(u, v)} is outside 0..{n_qubits - 1}")
        if u == v:
            raise ValueError("self-loops are not supported")
        canonical = (min(u, v), max(u, v))
        if canonical in seen:
            raise ValueError(f"duplicate undirected edge {canonical}")
        seen.add(canonical)
        clean_edges.append(canonical)

    if edge_weights is None:
        weights = np.ones(len(clean_edges), dtype=np.float64)
    else:
        weights = np.asarray(edge_weights, dtype=np.float64)
        if weights.shape != (len(clean_edges),):
            raise ValueError("edge_weights must contain one value per edge")
        if not np.all(np.isfinite(weights)):
            raise ValueError("edge_weights must be finite")
    return tuple(clean_edges), weights


def _validate_angles(gammas: Sequence[float], betas: Sequence[float]) -> tuple[Array, Array]:
    gamma_array = np.asarray(gammas, dtype=np.float64)
    beta_array = np.asarray(betas, dtype=np.float64)
    if gamma_array.ndim != 1 or beta_array.ndim != 1:
        raise ValueError("gammas and betas must be one-dimensional")
    if gamma_array.shape != beta_array.shape:
        raise ValueError("gammas and betas must have the same length")
    if not np.all(np.isfinite(gamma_array)) or not np.all(np.isfinite(beta_array)):
        raise ValueError("angles must be finite")
    return gamma_array, beta_array


def _validate_order(n_qubits: int, qubit_order: Sequence[int] | None) -> tuple[int, ...]:
    if qubit_order is None:
        return tuple(range(n_qubits))
    order = tuple(int(q) for q in qubit_order)
    if sorted(order) != list(range(n_qubits)):
        raise ValueError("qubit_order must be a permutation of range(n_qubits)")
    return order


def mis_cost_energies(
    n_qubits: int,
    edges: Iterable[tuple[int, int]],
    *,
    penalty: float = 2.0,
    edge_weights: Sequence[float] | Array | None = None,
) -> Array:
    """Return the diagonal MIS cost energy for every computational basis state."""

    clean_edges, weights = _validate_problem(n_qubits, edges, edge_weights)
    if not np.isfinite(penalty) or penalty < 0:
        raise ValueError("penalty must be finite and non-negative")

    dimension = 1 << int(n_qubits)
    basis = np.arange(dimension, dtype=np.uint64)
    occupations = ((basis[:, None] >> np.arange(n_qubits, dtype=np.uint64)) & 1).astype(
        np.float64
    )
    energies = -occupations.sum(axis=1)
    for (u, v), weight in zip(clean_edges, weights, strict=True):
        energies += float(penalty) * float(weight) * occupations[:, u] * occupations[:, v]
    return energies


def _apply_x_mixer(state: Array, beta: float, n_qubits: int) -> None:
    cosine = float(np.cos(beta))
    sine = float(np.sin(beta))
    dimension = state.size
    for qubit in range(n_qubits):
        stride = 1 << qubit
        block = stride << 1
        offsets = np.arange(stride)
        for start in range(0, dimension, block):
            zero_indices = start + offsets
            one_indices = zero_indices + stride
            zero = state[zero_indices].copy()
            one = state[one_indices].copy()
            state[zero_indices] = cosine * zero - 1j * sine * one
            state[one_indices] = cosine * one - 1j * sine * zero


def truncate_state_tt_svd(
    state: Sequence[complex] | Array,
    n_qubits: int,
    *,
    qubit_order: Sequence[int] | None = None,
    max_bond: int | None = None,
    relative_cutoff: float = 0.0,
    renormalize: bool = True,
    return_diagnostics: bool = False,
) -> Array | tuple[Array, dict[str, Any]]:
    """Compress and reconstruct a state with TT-SVD in an arbitrary qubit order.

    ``relative_cutoff`` is a per-cut relative Frobenius-norm tolerance: the
    smallest rank whose discarded squared singular-value mass is at most
    ``relative_cutoff**2`` times the total cut mass is retained.  ``max_bond``
    is then applied as a hard cap.  Setting no cap and a zero cutoff reconstructs
    the input to floating-point precision for every qubit permutation.
    """

    vector = np.asarray(state, dtype=np.complex128)
    if vector.shape != (1 << int(n_qubits),):
        raise ValueError("state length must equal 2**n_qubits")
    if not np.all(np.isfinite(vector)):
        raise ValueError("state must be finite")
    order = _validate_order(int(n_qubits), qubit_order)
    if max_bond is not None and (not isinstance(max_bond, (int, np.integer)) or max_bond < 1):
        raise ValueError("max_bond must be a positive integer or None")
    if not np.isfinite(relative_cutoff) or not 0.0 <= relative_cutoff <= 1.0:
        raise ValueError("relative_cutoff must lie in [0, 1]")

    input_norm = float(np.linalg.norm(vector))
    if input_norm == 0.0:
        raise ValueError("cannot truncate the zero state")

    # Fortran reshape maps tensor axis q to little-endian qubit q.
    little_endian_tensor = vector.reshape((2,) * int(n_qubits), order="F")
    ordered_tensor = np.transpose(little_endian_tensor, axes=order)

    cores: list[Array] = []
    kept_ranks: list[int] = []
    discarded_weights: list[float] = []
    work = ordered_tensor
    left_rank = 1
    for site in range(int(n_qubits) - 1):
        matrix = work.reshape(left_rank * 2, -1)
        u, singular_values, vh = np.linalg.svd(matrix, full_matrices=False)
        keep = singular_values.size
        if relative_cutoff > 0.0:
            allowed = (relative_cutoff * np.linalg.norm(singular_values)) ** 2
            reverse_tail = np.cumsum(np.square(singular_values[::-1]))
            discarded_count = int(np.searchsorted(reverse_tail, allowed, side="right"))
            keep = max(1, singular_values.size - discarded_count)
        if max_bond is not None:
            keep = min(keep, int(max_bond))

        discarded = singular_values[keep:]
        discarded_weights.append(float(np.vdot(discarded, discarded).real))
        kept_ranks.append(int(keep))
        cores.append(u[:, :keep].reshape(left_rank, 2, keep))
        remaining_sites = int(n_qubits) - site - 1
        work = (singular_values[:keep, None] * vh[:keep, :]).reshape(
            (keep,) + (2,) * remaining_sites
        )
        left_rank = keep

    cores.append(work.reshape(left_rank, 2, 1))
    reconstructed = cores[0]
    for core in cores[1:]:
        reconstructed = np.tensordot(reconstructed, core, axes=([-1], [0]))
    ordered_reconstructed = np.squeeze(reconstructed, axis=(0, -1))
    inverse_order = np.argsort(order)
    little_endian_reconstructed = np.transpose(ordered_reconstructed, axes=inverse_order)
    output = little_endian_reconstructed.reshape(-1, order="F")

    pre_renormalization_norm = float(np.linalg.norm(output))
    if renormalize:
        if pre_renormalization_norm == 0.0:
            raise FloatingPointError("TT-SVD produced a zero state")
        output = output / pre_renormalization_norm

    diagnostics: dict[str, Any] = {
        "qubit_order": list(order),
        "kept_ranks": kept_ranks,
        "max_kept_rank": max(kept_ranks, default=1),
        "discarded_weight_by_cut": discarded_weights,
        "discarded_weight_sum": float(sum(discarded_weights)),
        "input_norm": input_norm,
        "pre_renormalization_norm": pre_renormalization_norm,
        "output_norm": float(np.linalg.norm(output)),
    }
    if return_diagnostics:
        return output, diagnostics
    return output


def qaoa_mis_statevector(
    n_qubits: int,
    edges: Iterable[tuple[int, int]],
    gammas: Sequence[float],
    betas: Sequence[float],
    *,
    penalty: float = 2.0,
    edge_weights: Sequence[float] | Array | None = None,
    qubit_order: Sequence[int] | None = None,
    max_bond: int | None = None,
    relative_cutoff: float = 0.0,
    truncate_after: Sequence[str] = ("cost_layer", "mixer_layer"),
    return_diagnostics: bool = False,
) -> Array | tuple[Array, dict[str, Any]]:
    """Simulate QAOA-MIS with optional layerwise TT-SVD truncation.

    The preregistered default compresses after both sublayers of every QAOA
    layer.  ``truncate_after`` remains configurable only for explicit ablations.
    """

    clean_edges, weights = _validate_problem(n_qubits, edges, edge_weights)
    gamma_array, beta_array = _validate_angles(gammas, betas)
    order = _validate_order(int(n_qubits), qubit_order)
    stages = tuple(str(stage) for stage in truncate_after)
    allowed_stages = {"cost_layer", "mixer_layer"}
    if len(stages) != len(set(stages)) or not set(stages).issubset(allowed_stages):
        raise ValueError(
            "truncate_after must contain unique values drawn from "
            "{'cost_layer', 'mixer_layer'}"
        )
    energies = mis_cost_energies(
        int(n_qubits), clean_edges, penalty=penalty, edge_weights=weights
    )

    dimension = 1 << int(n_qubits)
    state = np.full(dimension, 1.0 / np.sqrt(dimension), dtype=np.complex128)
    truncation_enabled = bool(stages) and (max_bond is not None or relative_cutoff > 0.0)
    layer_diagnostics: list[dict[str, Any]] = []

    for layer, (gamma, beta) in enumerate(zip(gamma_array, beta_array, strict=True)):
        state *= np.exp(-1j * float(gamma) * energies)
        if truncation_enabled and "cost_layer" in stages:
            state, tt_info = truncate_state_tt_svd(
                state,
                int(n_qubits),
                qubit_order=order,
                max_bond=max_bond,
                relative_cutoff=relative_cutoff,
                renormalize=True,
                return_diagnostics=True,
            )
            tt_info["layer"] = layer
            tt_info["stage"] = "cost_layer"
            layer_diagnostics.append(tt_info)

        _apply_x_mixer(state, float(beta), int(n_qubits))
        if truncation_enabled and "mixer_layer" in stages:
            state, tt_info = truncate_state_tt_svd(
                state,
                int(n_qubits),
                qubit_order=order,
                max_bond=max_bond,
                relative_cutoff=relative_cutoff,
                renormalize=True,
                return_diagnostics=True,
            )
            tt_info["layer"] = layer
            tt_info["stage"] = "mixer_layer"
            layer_diagnostics.append(tt_info)

    # Unitary evolution is normalized analytically; remove only roundoff drift.
    norm = float(np.linalg.norm(state))
    if norm == 0.0:
        raise FloatingPointError("QAOA evolution produced a zero state")
    state = state / norm
    diagnostics = {
        "n_qubits": int(n_qubits),
        "depth": int(gamma_array.size),
        "qubit_order": list(order),
        "max_bond": None if max_bond is None else int(max_bond),
        "relative_cutoff": float(relative_cutoff),
        "truncate_after": list(stages),
        "truncated": truncation_enabled,
        "layers": layer_diagnostics,
        "truncations": layer_diagnostics,
        "final_norm": float(np.linalg.norm(state)),
    }
    if return_diagnostics:
        return state, diagnostics
    return state


def exact_qaoa_mis_statevector(
    n_qubits: int,
    edges: Iterable[tuple[int, int]],
    gammas: Sequence[float],
    betas: Sequence[float],
    *,
    penalty: float = 2.0,
    edge_weights: Sequence[float] | Array | None = None,
) -> Array:
    """Convenience wrapper for exact, untruncated QAOA-MIS evolution."""

    return qaoa_mis_statevector(
        n_qubits,
        edges,
        gammas,
        betas,
        penalty=penalty,
        edge_weights=edge_weights,
    )


def _event_mask(dimension: int, event: Event) -> Array:
    if callable(event):
        return np.fromiter((bool(event(i)) for i in range(dimension)), dtype=bool, count=dimension)

    if isinstance(event, np.ndarray) and event.dtype == bool:
        if event.shape != (dimension,):
            raise ValueError("boolean event mask must match the state dimension")
        return event.copy()

    mask = np.zeros(dimension, dtype=bool)
    for item in event:
        index = int(item, 2) if isinstance(item, str) else int(item)
        if not 0 <= index < dimension:
            raise ValueError(f"event basis index {index} is out of range")
        mask[index] = True
    return mask


def event_probability(
    state_or_probabilities: Sequence[complex] | Array,
    event: Event,
    *,
    probabilities: bool = False,
) -> float:
    """Return the normalized probability mass of an event.

    Pass ``probabilities=True`` for a classical probability vector (for
    example, the output of :func:`hardware_surrogate_distribution`).
    """

    values = np.asarray(state_or_probabilities)
    if values.ndim != 1 or values.size < 2 or values.size & (values.size - 1):
        raise ValueError("input must be a one-dimensional power-of-two vector")
    mask = _event_mask(values.size, event)
    if probabilities:
        masses = np.asarray(values, dtype=np.float64)
        if np.any(masses < -1e-15) or not np.all(np.isfinite(masses)):
            raise ValueError("probabilities must be finite and non-negative")
        masses = np.maximum(masses, 0.0)
    else:
        amplitudes = np.asarray(values, dtype=np.complex128)
        if not np.all(np.isfinite(amplitudes)):
            raise ValueError("state must be finite")
        masses = np.abs(amplitudes) ** 2
    total = float(masses.sum())
    if total <= 0.0:
        raise ValueError("input has zero total probability")
    result = float(masses[mask].sum() / total)
    return float(np.clip(result, 0.0, 1.0))


def maximum_independent_set_indices(
    n_qubits: int, edges: Iterable[tuple[int, int]]
) -> tuple[int, ...]:
    """Enumerate basis indices encoding maximum independent sets."""

    clean_edges, _ = _validate_problem(n_qubits, edges)
    best_size = -1
    best: list[int] = []
    for index in range(1 << int(n_qubits)):
        if any(((index >> u) & 1) and ((index >> v) & 1) for u, v in clean_edges):
            continue
        size = int(index.bit_count())
        if size > best_size:
            best_size = size
            best = [index]
        elif size == best_size:
            best.append(index)
    return tuple(best)


def apply_readout_flips(
    probabilities: Sequence[float] | Array,
    n_qubits: int,
    flip_probability: float | Sequence[float] | Array,
) -> Array:
    """Apply independent symmetric bit-flip readout channels."""

    distribution = np.asarray(probabilities, dtype=np.float64).copy()
    if distribution.shape != (1 << int(n_qubits),):
        raise ValueError("probability vector length must equal 2**n_qubits")
    if np.any(distribution < -1e-15) or not np.all(np.isfinite(distribution)):
        raise ValueError("probabilities must be finite and non-negative")
    distribution = np.maximum(distribution, 0.0)
    total = float(distribution.sum())
    if total <= 0.0:
        raise ValueError("probabilities must have positive mass")
    distribution /= total

    flips = np.asarray(flip_probability, dtype=np.float64)
    if flips.ndim == 0:
        flips = np.full(int(n_qubits), float(flips))
    if flips.shape != (int(n_qubits),) or np.any((flips < 0.0) | (flips > 1.0)):
        raise ValueError("flip_probability must be in [0, 1], scalar or per-qubit")

    dimension = distribution.size
    for qubit, flip in enumerate(flips):
        stride = 1 << qubit
        block = stride << 1
        offsets = np.arange(stride)
        updated = distribution.copy()
        for start in range(0, dimension, block):
            zero_indices = start + offsets
            one_indices = zero_indices + stride
            zero = distribution[zero_indices]
            one = distribution[one_indices]
            updated[zero_indices] = (1.0 - flip) * zero + flip * one
            updated[one_indices] = (1.0 - flip) * one + flip * zero
        distribution = updated
    return distribution / distribution.sum()


def hardware_surrogate_distribution(
    n_qubits: int,
    edges: Iterable[tuple[int, int]],
    gammas: Sequence[float],
    betas: Sequence[float],
    *,
    penalty: float = 2.0,
    edge_weights: Sequence[float] | Array | None = None,
    qubit_order: Sequence[int] | None = None,
    max_bond: int | None = None,
    relative_cutoff: float = 0.0,
    truncate_after: Sequence[str] = ("cost_layer", "mixer_layer"),
    angle_sigma: float = 0.0,
    edge_sigma: float = 0.0,
    readout_flip: float | Sequence[float] | Array = 0.0,
    depolarizing: float = 0.0,
    seed: int = 0,
    return_metadata: bool = False,
) -> Array | tuple[Array, dict[str, Any]]:
    """Return a deterministic noisy measurement distribution.

    A seeded draw creates fixed (coherent) additive perturbations for every
    gamma, beta and edge weight.  The resulting pure-state distribution is
    mixed with the uniform distribution and finally passed through independent
    symmetric readout flips.  Repeating a call with the same inputs and seed is
    bit-for-bit deterministic on the same NumPy implementation.
    """

    clean_edges, base_weights = _validate_problem(n_qubits, edges, edge_weights)
    gamma_array, beta_array = _validate_angles(gammas, betas)
    for name, value in (("angle_sigma", angle_sigma), ("edge_sigma", edge_sigma)):
        if not np.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and non-negative")
    if not np.isfinite(depolarizing) or not 0.0 <= depolarizing <= 1.0:
        raise ValueError("depolarizing must lie in [0, 1]")

    rng = np.random.default_rng(int(seed))
    noisy_gammas = gamma_array + rng.normal(0.0, float(angle_sigma), gamma_array.shape)
    noisy_betas = beta_array + rng.normal(0.0, float(angle_sigma), beta_array.shape)
    noisy_weights = base_weights + rng.normal(0.0, float(edge_sigma), base_weights.shape)

    state = qaoa_mis_statevector(
        int(n_qubits),
        clean_edges,
        noisy_gammas,
        noisy_betas,
        penalty=penalty,
        edge_weights=noisy_weights,
        qubit_order=qubit_order,
        max_bond=max_bond,
        relative_cutoff=relative_cutoff,
        truncate_after=truncate_after,
    )
    distribution = np.abs(state) ** 2
    dimension = distribution.size
    distribution = (1.0 - float(depolarizing)) * distribution + float(depolarizing) / dimension
    distribution = apply_readout_flips(distribution, int(n_qubits), readout_flip)
    distribution /= distribution.sum()

    metadata: dict[str, Any] = {
        "seed": int(seed),
        "noisy_gammas": noisy_gammas.tolist(),
        "noisy_betas": noisy_betas.tolist(),
        "noisy_edge_weights": noisy_weights.tolist(),
        "angle_sigma": float(angle_sigma),
        "edge_sigma": float(edge_sigma),
        "depolarizing": float(depolarizing),
    }
    if return_metadata:
        return distribution, metadata
    return distribution


def hardware_surrogate_event_probability(event: Event, **simulation_kwargs: Any) -> float:
    """Convenience wrapper returning one event mass from the noisy surrogate."""

    distribution = hardware_surrogate_distribution(**simulation_kwargs)
    return event_probability(distribution, event, probabilities=True)


# Short alias for callers that treat the full surrogate as one operation.
apply_hardware_surrogate = hardware_surrogate_distribution
