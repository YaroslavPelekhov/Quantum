"""Global linear decision-balanced reduced contraction oracle."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import linalg


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "experiments" / "decision_balanced_truncation"))

from dbt_core import (
    apply_gate_batch,
    backward_observability,
    hankel_singular_values,
    psd_square_root,
    reduced_gram,
    select_hankel_rank,
)


ALLOWED_RANKS = tuple(range(1, 9))
ENERGY_FRACTION = 0.99


def balanced_factors(
    reachability: np.ndarray, observability: np.ndarray, rank: int
) -> tuple[np.ndarray, np.ndarray, dict]:
    x = psd_square_root(reachability)
    y = psd_square_root(observability)
    u, singular, vh = linalg.svd(y.conj().T @ x, full_matrices=False, check_finite=False)
    if np.count_nonzero(singular > 1e-12) < rank:
        return orthogonal_factors(reachability, rank) + ({
            "fallback": True,
            "biorthogonality_error": 0.0,
            "hankel_singular_values": singular,
        },)
    scale = 1.0 / np.sqrt(singular[:rank])
    trial = (x @ vh.conj().T[:, :rank]) * scale
    test = (y @ u[:, :rank]) * scale
    error = float(np.linalg.norm(test.conj().T @ trial - np.eye(rank)))
    return trial, test, {
        "fallback": False,
        "biorthogonality_error": error,
        "hankel_singular_values": singular,
    }


def orthogonal_factors(reachability: np.ndarray, rank: int) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = linalg.eigh(reachability, check_finite=False)
    basis = vectors[:, np.argsort(values)[::-1][:rank]]
    return basis, basis


def exact_gramians_and_ranks(circuit_a, circuit_b, indices: list[int], cut: int):
    sites = circuit_a.num_qubits
    obs_a = backward_observability(circuit_a, indices, cut)
    obs_b = backward_observability(circuit_b, indices, cut)
    states = np.zeros((1 << sites, 2), dtype=np.complex128)
    states[0, :] = 1.0
    rows = []
    for position, (item_a, item_b) in enumerate(zip(circuit_a.data, circuit_b.data)):
        qargs_a = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        qargs_b = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
        states[:, 0] = apply_gate_batch(states[:, 0], item_a.operation, qargs_a, sites)
        states[:, 1] = apply_gate_batch(states[:, 1], item_b.operation, qargs_b, sites)
        reachability = 0.5 * reduced_gram(states, cut)
        observability = 0.5 * (obs_a[position] + obs_b[position]) / len(indices)
        singular = hankel_singular_values(reachability, observability)
        rank = select_hankel_rank(singular, ALLOWED_RANKS, ENERGY_FRACTION)
        rows.append((reachability, observability, rank))
    return rows


def build_bases(gramians, method: str):
    bases = []
    maximum_biorthogonality = 0.0
    fallbacks = 0
    for reachability, observability, rank in gramians:
        if method == "global_balanced":
            trial, test, info = balanced_factors(reachability, observability, rank)
            maximum_biorthogonality = max(
                maximum_biorthogonality, info["biorthogonality_error"]
            )
            fallbacks += int(info["fallback"])
        elif method == "orthogonal_baseline":
            trial, test = orthogonal_factors(reachability, rank)
        else:
            raise ValueError(method)
        bases.append((trial, test))
    return bases, {
        "maximum_biorthogonality_error": maximum_biorthogonality,
        "fallback_count": fallbacks,
    }


def global_reduced_contraction(circuit_a, circuit_b, bases, cut: int) -> np.ndarray:
    sites = circuit_a.num_qubits
    left = 1 << cut
    right = 1 << (sites - cut)
    initial = np.zeros((1 << sites, 2), dtype=np.complex128)
    initial[0, :] = 1.0
    coordinates = None
    previous_trial = None
    for position, ((item_a, item_b), (trial, test)) in enumerate(
        zip(zip(circuit_a.data, circuit_b.data), bases)
    ):
        if position == 0:
            full = initial
        else:
            full_tensor = np.einsum(
                "ak,krb->arb", previous_trial, coordinates, optimize=True
            )
            full = full_tensor.reshape(left * right, 2)
        qargs_a = tuple(circuit_a.find_bit(qubit).index for qubit in item_a.qubits)
        qargs_b = tuple(circuit_b.find_bit(qubit).index for qubit in item_b.qubits)
        full[:, 0] = apply_gate_batch(full[:, 0], item_a.operation, qargs_a, sites)
        full[:, 1] = apply_gate_batch(full[:, 1], item_b.operation, qargs_b, sites)
        tensor = full.reshape(left, right, 2)
        coordinates = np.einsum("ka,arb->krb", test.conj().T, tensor, optimize=True)
        previous_trial = trial
    reconstructed = np.einsum(
        "ak,krb->arb", previous_trial, coordinates, optimize=True
    ).reshape(left * right, 2)
    return reconstructed


def run_global_pair(circuit_a, circuit_b, indices: list[int], cut: int = 4) -> dict:
    gramians = exact_gramians_and_ranks(circuit_a, circuit_b, indices, cut)
    schedule = [row[2] for row in gramians]
    output = {
        "rank_schedule": schedule,
        "rank_min": min(schedule),
        "rank_max": max(schedule),
        "rank_mean": float(np.mean(schedule)),
        "equal_rank_cubed_work": int(sum(rank ** 3 for rank in schedule)),
        "methods": {},
    }
    for method in ("orthogonal_baseline", "global_balanced"):
        bases, diagnostics = build_bases(gramians, method)
        states = global_reduced_contraction(circuit_a, circuit_b, bases, cut)
        delta = float(
            (np.abs(states[indices, 1]) ** 2 - np.abs(states[indices, 0]) ** 2).sum()
        )
        output["methods"][method] = {
            "delta": delta,
            "final_norm_a": float(np.linalg.norm(states[:, 0])),
            "final_norm_b": float(np.linalg.norm(states[:, 1])),
            **diagnostics,
        }
    return output
