"""Optimize triple convolution against the first explicit multi-logical witness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


SINGLE_PAULI = (
    np.eye(2, dtype=complex),
    np.asarray([[0, 1], [1, 0]], dtype=complex),
    np.diag([1, -1]).astype(complex),
    np.asarray([[0, -1j], [1j, 0]], dtype=complex),
)


def pauli_matrix(label: int, qubits: int) -> np.ndarray:
    mask = (1 << qubits) - 1
    x, z = label & mask, label >> qubits
    output = np.asarray([[1.0 + 0.0j]])
    for index in range(qubits):
        symbol = ((x >> index) & 1) + 2 * ((z >> index) & 1)
        output = np.kron(output, SINGLE_PAULI[symbol])
    return output


def expectations(state: np.ndarray, operators: np.ndarray) -> np.ndarray:
    return np.real(np.einsum("i,kij,j->k", state.conj(), operators, state))


def maximize_trilinear(
    operators: np.ndarray, coefficients: np.ndarray, starts: int, steps: int, seed: int
):
    rng = np.random.default_rng(seed)
    dimension = operators.shape[1]
    best = -np.inf
    best_states = None
    for _ in range(starts):
        states = []
        for _copy in range(3):
            state = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
            states.append(state / np.linalg.norm(state))
        previous = -np.inf
        for _step in range(steps):
            for active in range(3):
                other = [index for index in range(3) if index != active]
                profile_left = expectations(states[other[0]], operators)
                profile_right = expectations(states[other[1]], operators)
                hamiltonian = np.einsum(
                    "k,kij->ij",
                    coefficients * profile_left * profile_right,
                    operators,
                )
                _, vectors = np.linalg.eigh(hamiltonian)
                states[active] = vectors[:, -1]
            profiles = [expectations(state, operators) for state in states]
            value = float(np.sum(coefficients * profiles[0] * profiles[1] * profiles[2]))
            if value > best:
                best = value
                best_states = [state.copy() for state in states]
            if value <= previous + 1e-13:
                break
            previous = value
    return best, best_states


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=5000)
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=660137)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    qubits = 3
    central = 37
    anticommuting = np.asarray([3, 14, 15, 16, 18])
    labels = np.asarray([3, 14, 15, 16, 18, 37, 38, 42, 43, 53, 55])
    coefficients = np.asarray([1, 1, 1, 1, 1, -1, 1, 1, -1, 1, 1], dtype=float)
    operators = np.stack([pauli_matrix(int(label), qubits) for label in labels])
    central_operator = pauli_matrix(central, qubits)
    factorization_errors = []
    partner_terms = []
    for axis in anticommuting:
        partner = central ^ int(axis)
        location = int(np.flatnonzero(labels == partner)[0])
        signed_partner = coefficients[location] * operators[location]
        factorization_errors.append(
            float(np.max(np.abs(signed_partner - central_operator @ pauli_matrix(int(axis), qubits))))
        )
        partner_terms.append([int(axis), partner, int(coefficients[location])])
    maximum, states = maximize_trilinear(
        operators, coefficients, args.starts, args.steps, args.seed
    )
    profiles = [expectations(state, operators) for state in states]
    payload = {
        "experiment": "triple_convolution_multilogical_integer_witness",
        "qubits": qubits,
        "seed": args.seed,
        "starts": args.starts,
        "steps": args.steps,
        "labels": labels.tolist(),
        "coefficients": coefficients.astype(int).tolist(),
        "analytic_structure": {
            "central_label": central,
            "pairwise_anticommuting_labels": anticommuting.tolist(),
            "axis_partner_coefficient": partner_terms,
            "maximum_matrix_factorization_error": max(factorization_errors),
            "identity": "W=-C+sum_j(A_j+C*A_j)",
            "odd_convolution_analytic_bound": 1,
        },
        "exact_stabilizer_vertex_bound": 1,
        "best_product_state_value": maximum,
        "status": "counterexample" if maximum > 1.0 + 1e-9 else "consistent_with_analytic_bound",
        "best_profiles": [profile.tolist() for profile in profiles],
        "best_state_real": [state.real.tolist() for state in states],
        "best_state_imag": [state.imag.tolist() for state in states],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
