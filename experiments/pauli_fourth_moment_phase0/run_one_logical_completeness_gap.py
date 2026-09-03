"""Test whether all one-logical stabilizer projections characterize STAB_n.

The test follows depolarizing rays rho(p)=(1-p)I/d+p|psi><psi| at n=3.
It compares the exact stabilizer-polytope entry threshold with the threshold at
which any rank-two stabilizer-code branch leaves the logical octahedron.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from stabilizer_core import (
    multiply_phase,
    pauli_expectations,
    random_state,
    stabilizer_gauge,
    stabilizer_matrix,
)


def commutes(left: int, right: int, qubits: int) -> bool:
    mask = (1 << qubits) - 1
    xl, zl = left & mask, left >> qubits
    xr, zr = right & mask, right >> qubits
    return ((xl & zr).bit_count() + (zl & xr).bit_count()) % 2 == 0


def subgroup(basis: tuple[int, ...], qubits: int) -> tuple[tuple[int, int], ...]:
    elements = [(1, 0)]
    for generator in basis:
        additions = []
        for phase, label in elements:
            extra_phase, extra_label = multiply_phase(label, generator, qubits)
            additions.append((phase * extra_phase, extra_label))
        elements += additions
    # Keep binary subset order: the syndrome character below is indexed by
    # the same generator bits.  Sorting by Pauli label would corrupt it.
    return tuple(elements)


def rank_two_codes(qubits: int, cache_dir: Path):
    if qubits != 3:
        raise ValueError("This audit is intentionally fixed at n=3")
    # Enumerate every two-dimensional isotropic subspace directly.  Merely
    # taking pairs from one stored basis of each Lagrangian misses subspaces.
    bases: dict[tuple[int, ...], tuple[int, ...]] = {}
    nonidentity = range(1, 1 << (2 * qubits))
    for left in nonidentity:
        for right in range(left + 1, 1 << (2 * qubits)):
            if not commutes(left, right, qubits):
                continue
            key = tuple(sorted((0, left, right, left ^ right)))
            bases.setdefault(key, (left, right))

    all_labels = range(1, 1 << (2 * qubits))
    output = []
    for labels, basis in bases.items():
        label_set = set(labels)
        centralizer = [
            p for p in all_labels if all(commutes(p, g, qubits) for g in basis)
        ]
        logical_x = next(p for p in centralizer if p not in label_set)
        logical_z = next(
            p
            for p in centralizer
            if p not in label_set and not commutes(p, logical_x, qubits)
        )
        logical_y = logical_x ^ logical_z
        output.append((subgroup(basis, qubits), (logical_x, logical_y, logical_z)))
    return output


def one_logical_threshold(coefficients: np.ndarray, codes, qubits: int):
    best = 1.0
    witness = None
    for group, logicals in codes:
        rank = len(group).bit_length() - 1
        for syndrome in range(1 << rank):
            denominator_nonidentity = 0.0
            numerators = np.zeros(3)
            for subset, (group_phase, label) in enumerate(group):
                eigenvalue = -1 if (subset & syndrome).bit_count() & 1 else 1
                signed_phase = group_phase * eigenvalue
                if label:
                    denominator_nonidentity += signed_phase * coefficients[label - 1]
                for axis, logical in enumerate(logicals):
                    product_phase, product_label = multiply_phase(label, logical, qubits)
                    numerators[axis] += (
                        signed_phase * product_phase * coefficients[product_label - 1]
                    )
            slope = float(np.abs(numerators).sum() - denominator_nonidentity)
            threshold = 1.0 if slope <= 1.0 else 1.0 / slope
            if threshold < best:
                best = threshold
                witness = {
                    "group": [label for _, label in group],
                    "group_phases": [phase for phase, _ in group],
                    "logical_xyz": list(logicals),
                    "syndrome": syndrome,
                    "denominator_slope": denominator_nonidentity,
                    "numerators": numerators.tolist(),
                    "inequality_slope": slope,
                }
    return best, witness


def audit_one_logical_point(
    coefficients: np.ndarray, codes, qubits: int, visibility: float
):
    max_excess = -np.inf
    min_branch_numerator = np.inf
    branches = 0
    for group, logicals in codes:
        rank = len(group).bit_length() - 1
        for syndrome in range(1 << rank):
            denominator_nonidentity = 0.0
            numerators = np.zeros(3)
            for subset, (group_phase, label) in enumerate(group):
                eigenvalue = -1 if (subset & syndrome).bit_count() & 1 else 1
                signed_phase = group_phase * eigenvalue
                if label:
                    denominator_nonidentity += signed_phase * coefficients[label - 1]
                for axis, logical in enumerate(logicals):
                    product_phase, product_label = multiply_phase(label, logical, qubits)
                    numerators[axis] += (
                        signed_phase * product_phase * coefficients[product_label - 1]
                    )
            branch_numerator = 1.0 + visibility * denominator_nonidentity
            excess = visibility * float(np.abs(numerators).sum()) - branch_numerator
            max_excess = max(max_excess, excess)
            min_branch_numerator = min(min_branch_numerator, branch_numerator)
            branches += 1
    return {
        "branches_checked": branches,
        "max_unnormalized_octahedron_excess": float(max_excess),
        "min_branch_probability_numerator": float(min_branch_numerator),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=660127)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    qubits = 3
    cache_dir = args.output.parent / ".cache"
    matrix, _ = stabilizer_matrix(qubits, cache_dir)
    codes = rank_two_codes(qubits, cache_dir)
    rng = np.random.default_rng(args.seed)
    best = None
    tested = 0
    for trial in range(args.trials):
        state = random_state(1 << qubits, rng)
        coefficients = pauli_expectations(state, qubits)
        one_threshold, one_witness = one_logical_threshold(coefficients, codes, qubits)
        gauge = stabilizer_gauge(matrix, coefficients)
        if not gauge.success:
            raise RuntimeError(gauge.message)
        global_threshold = min(1.0, 1.0 / float(gauge.fun))
        gap = one_threshold - global_threshold
        record = {
            "trial": trial,
            "global_stabilizer_threshold": global_threshold,
            "one_logical_threshold": one_threshold,
            "threshold_gap": gap,
            "pure_state_stabilizer_gauge": float(gauge.fun),
            "limiting_one_logical_witness": one_witness,
            "state_real": state.real.tolist(),
            "state_imag": state.imag.tolist(),
        }
        if best is None or gap > best["threshold_gap"]:
            best = record
        tested += 1

    assert best is not None
    midpoint = 0.5 * (
        best["global_stabilizer_threshold"] + best["one_logical_threshold"]
    )
    state = np.asarray(best["state_real"]) + 1j * np.asarray(best["state_imag"])
    coefficients = pauli_expectations(state, qubits)
    gauge = stabilizer_gauge(matrix, coefficients)
    dual = np.asarray(gauge.eqlin.marginals)
    dual_vertex_values = np.asarray(matrix.T @ dual).ravel()
    rounded_dual = np.rint(dual)
    rounded_vertex_values = np.asarray(matrix.T @ rounded_dual).ravel()
    best["certified_midpoint"] = midpoint
    best["midpoint_global_gauge"] = midpoint * best["pure_state_stabilizer_gauge"]
    best["midpoint_one_logical_margin"] = (
        best["one_logical_threshold"] - midpoint
    )
    best["midpoint_min_density_eigenvalue"] = (1.0 - midpoint) / (1 << qubits)
    best["midpoint_one_logical_audit"] = audit_one_logical_point(
        coefficients, codes, qubits, midpoint
    )
    best["global_dual_certificate"] = {
        "dual_objective_at_midpoint": float(midpoint * coefficients @ dual),
        "maximum_over_stabilizer_vertices": float(dual_vertex_values.max()),
        "maximum_dual_constraint_excess": float(dual_vertex_values.max() - 1.0),
        "minimum_over_stabilizer_vertices": float(dual_vertex_values.min()),
        "witness_coefficients": dual.tolist(),
        "integer_rounding_error": float(np.max(np.abs(dual - rounded_dual))),
        "integer_witness_nonzero": [
            [index + 1, int(value)]
            for index, value in enumerate(rounded_dual)
            if value
        ],
        "integer_witness_objective_at_midpoint": float(
            midpoint * coefficients @ rounded_dual
        ),
        "integer_witness_exact_maximum_over_vertices": int(
            rounded_vertex_values.max()
        ),
        "integer_witness_exact_minimum_over_vertices": int(
            rounded_vertex_values.min()
        ),
    }
    payload = {
        "experiment": "one_logical_tests_are_not_complete_for_STAB3",
        "qubits": qubits,
        "seed": args.seed,
        "trials": tested,
        "rank_two_codes": len(codes),
        "stabilizer_vertices": matrix.shape[1],
        "criterion": (
            "A positive threshold gap gives a physical depolarized pure state "
            "outside STAB_3 while every rank-two stabilizer-code branch is in "
            "the one-qubit stabilizer octahedron."
        ),
        "best": best,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if best["threshold_gap"] <= 1e-8:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
