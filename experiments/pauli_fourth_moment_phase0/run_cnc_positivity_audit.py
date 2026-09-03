"""Direct sign/normalization audit of odd-convolution CNC positivity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from stabilizer_core import multiply_phase, random_state


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


def gamma_labels(spin_qubits: int, total_qubits: int) -> list[int]:
    labels = []
    for pivot in range(spin_qubits):
        z_prefix = (1 << pivot) - 1
        labels.append((1 << pivot) | (z_prefix << total_qubits))
        labels.append((1 << pivot) | ((z_prefix | (1 << pivot)) << total_qubits))
    labels.append(((1 << spin_qubits) - 1) << total_qubits)
    return labels


def isotropic_group(
    spin_qubits: int, syndrome_qubits: int, syndrome_signs: np.ndarray
) -> list[tuple[int, int]]:
    total = spin_qubits + syndrome_qubits
    elements = [(1, 0)]
    for offset, sign in enumerate(syndrome_signs):
        generator = 1 << (total + spin_qubits + offset)
        additions = []
        for coefficient, label in elements:
            phase, product = multiply_phase(label, generator, total)
            additions.append((coefficient * int(sign) * phase, product))
        elements += additions
    return elements


def cnc_expansion(
    spin_qubits: int,
    syndrome_qubits: int,
    gamma_signs: np.ndarray,
    syndrome_signs: np.ndarray,
) -> list[tuple[int, int]]:
    total = spin_qubits + syndrome_qubits
    group = isotropic_group(spin_qubits, syndrome_qubits, syndrome_signs)
    terms = list(group)
    for gamma_sign, gamma in zip(gamma_signs, gamma_labels(spin_qubits, total)):
        for group_sign, stabilizer in group:
            phase, label = multiply_phase(gamma, stabilizer, total)
            terms.append((int(gamma_sign) * group_sign * phase, label))
    return terms


def expectation(state: np.ndarray, operator: np.ndarray) -> float:
    return float(np.vdot(state, operator @ state).real)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=300)
    parser.add_argument("--seed", type=int, default=660149)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    cases = []
    global_minimum = np.inf
    for spin_qubits in (1, 2, 3):
        for syndrome_qubits in (0, 1, 2):
            total = spin_qubits + syndrome_qubits
            dimension = 1 << total
            for order in (3, 5):
                minimum = np.inf
                for _ in range(args.trials):
                    gamma_signs = rng.choice((-1, 1), size=2 * spin_qubits + 1)
                    syndrome_signs = rng.choice((-1, 1), size=syndrome_qubits)
                    expansion = cnc_expansion(
                        spin_qubits, syndrome_qubits, gamma_signs, syndrome_signs
                    )
                    matrices = {
                        label: pauli_matrix(label, total) for _, label in expansion
                    }
                    inputs = [random_state(dimension, rng) for _ in range(order)]
                    value = 0.0
                    for sign, label in expansion:
                        product = np.prod(
                            [expectation(state, matrices[label]) for state in inputs]
                        )
                        value += sign * product
                    value /= dimension
                    minimum = min(minimum, float(value))
                cases.append(
                    {
                        "spin_qubits": spin_qubits,
                        "syndrome_qubits": syndrome_qubits,
                        "convolution_order": order,
                        "trials": args.trials,
                        "minimum_overlap": minimum,
                    }
                )
                global_minimum = min(global_minimum, minimum)
    payload = {
        "experiment": "canonical_maximal_CNC_odd_convolution_positivity",
        "seed": args.seed,
        "cases": cases,
        "total_random_instances": len(cases) * args.trials,
        "global_minimum_overlap": global_minimum,
        "status": "violation" if global_minimum < -1e-10 else "no_violation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if global_minimum < -1e-10:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
