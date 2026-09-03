"""Direct-matrix audit of the one-logical-qubit convolution proof identity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def random_density(dimension: int, rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    density = matrix @ matrix.conj().T
    return density / np.trace(density)


def random_pure_density(dimension: int, rng: np.random.Generator) -> np.ndarray:
    state = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
    state /= np.linalg.norm(state)
    return np.outer(state, state.conj())


def convolution_three(inputs: list[np.ndarray], qubits: int) -> np.ndarray:
    dimension = 1 << qubits
    total = dimension**3
    permutation = np.empty(total, dtype=np.int64)
    for first in range(dimension):
        for second in range(dimension):
            for third in range(dimension):
                source = (first * dimension + second) * dimension + third
                out_first = first ^ second ^ third
                out_second = second ^ first
                out_third = third ^ first
                permutation[source] = (
                    (out_first * dimension + out_second) * dimension + out_third
                )
    joint = np.kron(np.kron(inputs[0], inputs[1]), inputs[2])
    inverse = np.argsort(permutation)
    evolved = joint[np.ix_(inverse, inverse)]
    tensor = evolved.reshape(dimension, dimension * dimension, dimension, dimension * dimension)
    return np.einsum("aebe->ab", tensor)


def conditional_bloch(density: np.ndarray, syndrome: int, qubits: int):
    logical_bit = 1 << (qubits - 1)
    indices = (syndrome, syndrome | logical_bit)
    block = density[np.ix_(indices, indices)]
    probability = float(np.trace(block).real)
    if probability <= 1e-15:
        return probability, np.zeros(3)
    block /= probability
    bloch = np.asarray(
        [
            2.0 * block[0, 1].real,
            -2.0 * block[0, 1].imag,
            (block[0, 0] - block[1, 1]).real,
        ]
    )
    return probability, bloch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=3)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--seed", type=int, default=660121)
    parser.add_argument("--pure", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    syndrome_count = 1 << (args.qubits - 1)
    maximum_identity_error = 0.0
    maximum_octrahedron_excess = -np.inf
    minimum_branch_probability = 1.0
    for _ in range(args.trials):
        sampler = random_pure_density if args.pure else random_density
        inputs = [sampler(1 << args.qubits, rng) for _ in range(3)]
        # Proposition 13 of Bu--Gu--Jaffe adds full transpose for K=3.
        # Remove it here so the directly simulated output has pure coefficient
        # products, exactly as in the syndrome-Fourier proof.
        output = convolution_three(inputs, args.qubits).T
        conditional_inputs = [
            [conditional_bloch(density, syndrome, args.qubits) for syndrome in range(syndrome_count)]
            for density in inputs
        ]
        for output_syndrome in range(syndrome_count):
            direct_probability, direct_bloch = conditional_bloch(
                output, output_syndrome, args.qubits
            )
            numerator = np.zeros(3)
            mixture_probability = 0.0
            for first in range(syndrome_count):
                for second in range(syndrome_count):
                    third = output_syndrome ^ first ^ second
                    probabilities = [
                        conditional_inputs[0][first][0],
                        conditional_inputs[1][second][0],
                        conditional_inputs[2][third][0],
                    ]
                    weight = float(np.prod(probabilities))
                    mixture_probability += weight
                    numerator += weight * np.prod(
                        [
                            conditional_inputs[0][first][1],
                            conditional_inputs[1][second][1],
                            conditional_inputs[2][third][1],
                        ],
                        axis=0,
                    )
            mixture_bloch = numerator / mixture_probability
            error = max(
                abs(direct_probability - mixture_probability),
                float(np.max(np.abs(direct_bloch - mixture_bloch))),
            )
            maximum_identity_error = max(maximum_identity_error, error)
            maximum_octrahedron_excess = max(
                maximum_octrahedron_excess,
                float(np.sum(np.abs(mixture_bloch)) - 1.0),
            )
            minimum_branch_probability = min(minimum_branch_probability, direct_probability)
    payload = {
        "status": "pass" if maximum_identity_error < 1e-11 and maximum_octrahedron_excess <= 1e-12 else "fail",
        "qubits": args.qubits,
        "trials": args.trials,
        "branches": args.trials * syndrome_count,
        "seed": args.seed,
        "input_kind": "pure" if args.pure else "mixed_wishart",
        "maximum_identity_error": maximum_identity_error,
        "maximum_octahedron_excess": maximum_octrahedron_excess,
        "minimum_branch_probability": minimum_branch_probability,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
